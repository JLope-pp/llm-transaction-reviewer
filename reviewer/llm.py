import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "cache"

PRICES = {
    "nova-micro": (0.035, 0.14),
    "nova-lite": (0.06, 0.24),
    "nova-pro": (0.80, 3.20),
    "claude-haiku-4-5": (1.00, 5.00),
}
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
CACHED_MODEL = "eu.amazon.nova-lite-v1:0"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
RETRYABLE = {"ThrottlingException", "ServiceUnavailableException", "ModelTimeoutException",
             "InternalServerException", "ModelNotReadyException",
             "ModelErrorException"}


class CacheMiss(Exception):
    pass


class ProviderError(Exception):
    pass


def model_slug(model_id: str) -> str:
    for slug in PRICES:
        if slug in model_id:
            return slug
    return re.sub(r"[^a-z0-9]+", "-", model_id.lower()).strip("-")


def cost_usd(model_id: str, usage: dict) -> float:
    pin, pout = PRICES.get(model_slug(model_id), (0.0, 0.0))
    return (usage.get("inputTokens", 0) * pin + usage.get("outputTokens", 0) * pout) / 1e6


class LLM:
    def __init__(self, model_id: str, offline: bool = False, temperature: float = 0.0,
                 max_tokens: int = 6000):
        self.model_id = model_id
        self.offline = offline
        self.params = {"temperature": temperature, "maxTokens": max_tokens}
        self.path = CACHE_DIR / f"{model_slug(model_id)}.jsonl"
        self.cache = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                rec = json.loads(line)
                self.cache[rec["key"]] = rec
        self._client = None
        self.calls = {"cache_hits": 0, "api_calls": 0}

    def _key(self, system, user, tool) -> str:
        blob = json.dumps({"model": self.model_id, "system": system, "user": user,
                           "tool": tool, "params": self.params}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def client(self):
        if self._client is None:
            import boto3
            from botocore.config import Config
            self._client = boto3.client("bedrock-runtime", region_name=region(), config=Config(
                read_timeout=180, retries={"max_attempts": 1}))
        return self._client

    def call(self, system: str, user: str, tool: dict) -> dict:
        key = self._key(system, user, tool)
        cached = self.cache.get(key)
        if cached and not (cached.get("error") and not self.offline):
            self.calls["cache_hits"] += 1
            if cached.get("error"):
                raise ProviderError(cached["error"])
            return cached
        if self.offline:
            raise CacheMiss(key)

        started = time.time()
        try:
            if provider(self.model_id) == "anthropic":
                tool_input, text, usage, stop = self._anthropic(system, user, tool)
            else:
                tool_input, text, usage, stop = self._bedrock(system, user, tool)
        except ProviderError as e:
            self._append({"key": key, "model": self.model_id, "error": str(e), "cost_usd": 0,
                          "user_sha": hashlib.sha256(user.encode()).hexdigest()[:12]})
            raise
        self.calls["api_calls"] += 1
        rec = {
            "key": key, "model": self.model_id, "tool_input": tool_input, "text": text,
            "usage": usage, "stop_reason": stop,
            "latency_s": round(time.time() - started, 2),
            "user_sha": hashlib.sha256(user.encode()).hexdigest()[:12],
            "cost_usd": round(cost_usd(self.model_id, usage), 6),
        }
        self._append(rec)
        return rec

    def _append(self, rec: dict) -> None:
        CACHE_DIR.mkdir(exist_ok=True)
        with self.path.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        self.cache[rec["key"]] = rec

    def _bedrock(self, system: str, user: str, tool: dict):
        request = {
            "modelId": self.model_id,
            "system": [{"text": system}],
            "messages": [{"role": "user", "content": [{"text": user}]}],
            "inferenceConfig": self.params,
            "toolConfig": {"tools": [{"toolSpec": tool}], "toolChoice": {"tool": {"name": tool["name"]}}},
        }
        response = None
        for attempt in range(5):
            try:
                response = self.client().converse(**request)
                break
            except Exception as e:
                code = getattr(e, "response", {}).get("Error", {}).get("Code", type(e).__name__)
                if code not in RETRYABLE and "Timeout" not in code and "Connection" not in code:
                    raise ProviderError(f"{code}: {e}") from e
                time.sleep(min(2 ** attempt * 2, 30))
        if response is None:
            raise ProviderError("retries exhausted")
        content = response["output"]["message"]["content"]
        tool_input = next((b["toolUse"]["input"] for b in content if "toolUse" in b), None)
        text = "".join(b.get("text", "") for b in content)
        return tool_input, text, response.get("usage", {}), response.get("stopReason")

    def anthropic_body(self, system: str, user: str, tool: dict) -> dict:
        return {
            "model": self.model_id, "system": system,
            "max_tokens": self.params["maxTokens"], "temperature": self.params["temperature"],
            "messages": [{"role": "user", "content": user}],
            "tools": [{"name": tool["name"], "description": tool["description"],
                       "input_schema": tool["inputSchema"]["json"]}],
            "tool_choice": {"type": "tool", "name": tool["name"]},
        }

    def _anthropic(self, system: str, user: str, tool: dict):
        body = json.dumps(self.anthropic_body(system, user, tool)).encode()
        headers = {"x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""),
                   "anthropic-version": "2023-06-01", "content-type": "application/json"}
        response = None
        for attempt in range(5):
            try:
                req = urllib.request.Request(ANTHROPIC_URL, data=body, headers=headers)
                with urllib.request.urlopen(req, timeout=180) as r:
                    response = json.loads(r.read())
                break
            except urllib.error.HTTPError as e:
                if e.code not in (408, 429, 500, 502, 503, 504, 529):
                    raise ProviderError(f"HTTP {e.code}: {e.read()[:300]!r}") from e
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt == 4:
                    raise ProviderError(f"{type(e).__name__}: {e}") from e
            time.sleep(min(2 ** attempt * 2, 30))
        if response is None:
            raise ProviderError("retries exhausted")
        return parse_anthropic(response)


def parse_anthropic(response: dict):
    content = response.get("content", [])
    tool_input = next((b["input"] for b in content if b.get("type") == "tool_use"), None)
    text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
    u = response.get("usage", {})
    usage = {"inputTokens": u.get("input_tokens", 0), "outputTokens": u.get("output_tokens", 0)}
    return tool_input, text, usage, response.get("stop_reason")


def region() -> str | None:
    return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")


def provider(model_id: str) -> str:
    return "anthropic" if model_id.startswith("claude-") else "bedrock"


def _aws_credentials() -> bool:
    if os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        return True
    try:
        import boto3
        return boto3.Session().get_credentials() is not None
    except Exception:
        return False


def has_credentials(model_id: str) -> bool:
    if provider(model_id) == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    return _aws_credentials()


def default_model() -> str:
    if os.environ.get("MODEL_ID"):
        return os.environ["MODEL_ID"]
    if not _aws_credentials():
        return ANTHROPIC_MODEL if os.environ.get("ANTHROPIC_API_KEY") else CACHED_MODEL
    r = region() or "eu-"
    geo = "us" if r.startswith(("us-", "ca-")) else "apac" if r.startswith("ap-") else "eu"
    return f"{geo}.amazon.nova-lite-v1:0"
