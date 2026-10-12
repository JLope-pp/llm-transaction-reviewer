# LLM reviewer for keyword transaction labels

A keyword engine labels bank transactions in Plaid format. An LLM reads those labels, flags the
ones it doubts and suggests the right label with a reason an underwriter can read in five
seconds. Code decides which suggestions get applied, and then I measure what they're worth to a
funding decision.

I built this as the AI Engineer take-home for Fundo, a revenue-based lender for small
businesses.

[Versión en español](README.es.md)

## Requirements

You need Python 3.10 or newer. The only dependency is boto3:

```bash
pip install -r requirements.txt
```

## Reproduce the results without an API key

The LLM responses are committed in reviewer/cache/, so this replays them and regenerates every
output without calling any provider:

```bash
pip install -r requirements.txt
python run.py --use-cache
```

It prints monthly revenue and the offer for each business under the truth, the keyword engine
and the reviewer, along with the dollar error, flag precision, hard negatives and LLM spend. It
takes about 30 seconds, mostly the mislabel simulation.

| Output | What's in it |
|---|---|
| outputs/nova-lite/reviews.json | For each transaction: engine label, suggested label, final label, status, confidence, reason, evidence |
| outputs/nova-lite/metrics.json | Monthly revenue error per business, flag precision and recall, hard negatives, injection cases |
| outputs/credit/report.md | Part 2: features and offers before and after, mislabel simulation at 2, 5 and 10% |

## Run it with an LLM

The provider depends on what you have in the environment:

| Environment | Provider | Model |
|---|---|---|
| AWS_BEARER_TOKEN_BEDROCK and AWS_REGION | Amazon Bedrock (default) | Nova Lite |
| ANTHROPIC_API_KEY, without AWS credentials | Anthropic API | Claude Haiku 4.5 |
| Nothing | Cache only, with a warning | |

```bash
export AWS_BEARER_TOKEN_BEDROCK=...   # a Bedrock API key
export AWS_REGION=us-east-1
python run.py
```

Bedrock also works with any standard AWS credential (AWS_PROFILE, or AWS_ACCESS_KEY_ID and
AWS_SECRET_ACCESS_KEY). The Nova Lite inference profile follows your region (us., eu. or
apac.). MODEL_ID overrides the model: ids starting with claude- go to the Anthropic API and
anything else goes to Bedrock. New responses get appended to the cache, and anything already in
it is never requested again.

## Other datasets

```bash
python run.py --use-cache --data data/holdout2   # also data/holdout, data/holdout3, data/holdout4
```

This runs the same pipeline on another labeled dataset and writes to outputs/ under the
dataset's name. I wrote holdout 1 after freezing the reviewer; holdouts 2 to 4 were written by a
separate agent that never saw it (SOLUTION.md has the details). python -m data.holdout, and the
same for holdout2 to holdout4, regenerates them.

## Review your own transactions

```bash
python run.py --input transactions.json                      # review only
python run.py --input transactions.json --truth labels.json  # review and score
python run.py --input transactions.json --assets asset_report.json --owner "Jane Doe" --name "Acme LLC"
```

The input can be a Plaid /transactions/get or /transactions/sync response, a plain list of Plaid
transactions, or a folder laid out like data/generated (businesses.json plus the files).
Pending transactions are dropped, and missing optional fields get Plaid's empty values. For each
business it prints the flagged groups the way an underwriter would see them, the features and
offer with the engine's labels and with the reviewer's, the balance signals, and the decision
(fund, decline or refer). The asset report adds the daily balances, and the owner and business
name enable the checks that need them. Without those, the checks are skipped and
business/personal changes go to an underwriter.

Passing a truth file scores the run the same way as the bundled datasets (dollar error, flag
precision and recall, harmful corrections, wrong decisions) and lists the costliest errors that
are left. It can be a dictionary from transaction_id to label, or a list of objects with a
transaction_id. A label can be a group name, either mine (hr_gambling) or the brief's (High risk,
gambling), or an object with group, label or category, is_business and optionally revenue. A
truth file with only revenue yes/no also works. Results go to outputs/input/ under the file's
name.

## Step by step

run.py chains these, and each one also runs on its own:

```bash
python -m data.generate      # synthetic Plaid data: 10 businesses, 61-90 days, truth kept apart
python -m engine.keywords    # keyword engine labels + its error against the truth
python -m reviewer.review    # LLM reviewer (--offline for cache only, --model, --input)
python -m reviewer.evaluate  # scores the reviewer against the truth
python -m credit.simulate    # Part 2
```

The generated data is committed in data/generated/. If you regenerate it with a different seed
the transactions change and the cache no longer matches.

## Layout

| Path | What it does |
|---|---|
| data/ | Synthetic Plaid-format generators and the loader |
| engine/ | The keyword engine, imperfect on purpose |
| reviewer/ | Prompt, LLM client with cache, evidence guardrails, policy, evaluation |
| credit/ | Credit features, offer rule, decision rule, mislabel simulation |
| labels.py | The 13 groups and the revenue rule, shared by everything |
| run.py | The single command |

Decisions, results and limitations are in [SOLUTION.md](SOLUTION.md) ([español](SOLUTION.es.md)).
