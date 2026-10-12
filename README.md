# LLM reviewer for keyword transaction labels

A keyword engine labels bank transactions in Plaid format. An LLM reviews those labels,
flags the ones it doubts and proposes the correct label with a reason an underwriter can
read in five seconds. Code decides which corrections are applied. Then we measure what the
corrections are worth to a funding decision.

Built as the AI Engineer take-home for Fundo, a revenue-based lender for small businesses.

[Versión en español](README.es.md)

## Requirements

- Python 3.10+
- `pip install -r requirements.txt` (only `boto3`)

## Reproduce the results without an API key

LLM responses are committed in `reviewer/cache/`. This replays them and regenerates every
output, with no key and no provider call:

```bash
pip install -r requirements.txt
python run.py --use-cache
```

It prints, per business, monthly revenue and offer under the truth, the keyword engine and
the reviewer, plus the dollar error, flag precision, hard negatives and the LLM spend. Takes
about 30 seconds (most of it is the mislabel simulation).

| Output | Content |
|---|---|
| `outputs/nova-lite/reviews.json` | Per transaction: engine label, proposed label, final label, status, confidence, reason, evidence |
| `outputs/nova-lite/metrics.json` | Monthly revenue error per business, flag precision/recall, hard negatives, injection cases |
| `outputs/credit/report.md` | Part 2: features and offer before/after, mislabel simulation at 2/5/10% |

## Run with an LLM

The provider is picked from the environment:

| Environment | Provider | Model |
|---|---|---|
| `AWS_BEARER_TOKEN_BEDROCK` + `AWS_REGION` | Amazon Bedrock (default) | Nova Lite |
| `ANTHROPIC_API_KEY` (no AWS credentials) | Anthropic API | Claude Haiku 4.5 |
| none | cache only, with a warning | |

```bash
export AWS_BEARER_TOKEN_BEDROCK=...   # a Bedrock API key
export AWS_REGION=us-east-1
python run.py
```

Bedrock also accepts any standard AWS credential (`AWS_PROFILE`, `AWS_ACCESS_KEY_ID` /
`AWS_SECRET_ACCESS_KEY`). The Nova Lite inference profile follows the region (`us.`, `eu.`,
`apac.`). `MODEL_ID` overrides the model: ids starting with `claude-` go to the Anthropic
API, anything else to Bedrock. New responses are appended to the cache; cached ones are
never requested again.

## Other datasets

```bash
python run.py --use-cache --data data/holdout2   # also data/holdout, data/holdout3, data/holdout4
```

Same pipeline on another labeled dataset; outputs go to `outputs/<dataset>/`. Holdout 1 was
written after the reviewer was frozen; holdouts 2-4 by a separate agent that never saw the
reviewer (see SOLUTION.md). `python -m data.holdout` (and `holdout2..4`) regenerates them.

## Review your own transactions

```bash
python run.py --input transactions.json                      # review only
python run.py --input transactions.json --truth labels.json  # review and score
python run.py --input transactions.json --assets asset_report.json --owner "Jane Doe" --name "Acme LLC"
```

`--input` takes a Plaid `/transactions/get` or `/transactions/sync` response, a plain list of
Plaid transactions, or a folder laid out like `data/generated` (`businesses.json` + files).
Pending transactions are dropped and missing optional fields are filled with Plaid's empty
values. Per business it prints the flagged groups as an underwriter would see them (engine
label, proposed label, revenue yes/no, confidence, reason, evidence), the features and offer
with the engine's labels and with the reviewer's, the balance signals and our decision
(fund / decline / refer). `--assets` adds the daily balances; `--owner` and `--name` add the
application data the owner and business-name checks need. Without them those checks are
skipped and business/personal changes go to an underwriter.

`--truth` scores the run the same way as our datasets (dollar error, flag precision and
recall, harmful corrections, wrong decisions) and lists the costliest errors left. It accepts
`{transaction_id: label}` or a list of objects with `transaction_id`; a label is a group name,
ours (`hr_gambling`) or the brief's (`High risk — gambling`), or an object with
`group`/`label`/`category`, `is_business` and optionally `revenue`. Revenue-only truth works too.
Output goes to `outputs/input/<name>/`.

## Step by step

`run.py` chains these; each also runs alone:

```bash
python -m data.generate      # synthetic Plaid data: 10 businesses, 61-90 days, truth kept apart
python -m engine.keywords    # keyword engine labels + its error against the truth
python -m reviewer.review    # LLM reviewer (--offline for cache only, --model, --input)
python -m reviewer.evaluate  # scores the reviewer against the truth
python -m credit.simulate    # Part 2
```

The generated data is committed in `data/generated/`. Regenerating it with another seed
changes the transactions, and the cache no longer matches.

## Layout

| Path | What it does |
|---|---|
| `data/` | Synthetic Plaid-format generator and loader |
| `engine/` | Keyword engine, deliberately imperfect |
| `reviewer/` | Prompt, LLM client with cache, evidence guardrails, policy, evaluation |
| `credit/` | Credit features, offer rule, mislabel simulation |
| `labels.py` | The 13 groups and the revenue rule, shared by everything |
| `run.py` | The single command |

Decisions, results and limitations: [SOLUTION.md](SOLUTION.md) ([español](SOLUTION.es.md)).
