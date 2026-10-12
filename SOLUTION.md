# Solution

[Versión en español](SOLUTION.es.md)

An LLM reviews a keyword engine's labels on Plaid-format transactions. Code decides which
corrections are applied, and a decision rule uses the account balance as a second opinion,
so one wrong label cannot get a business funded by itself. Everything reproduces with
`python run.py --use-cache` (other datasets via `--data`), no key needed.

**Headline (Nova Lite, 36 businesses in five datasets, three of them blind):** the reviewer
never turned a right label wrong, and our decision rule funded none of the businesses that
should get $0. The engine alone funds 8 of them.

## Data and engine

Synthetic `/transactions/get` and `/asset_report/get` responses (Plaid sign convention,
PFC v2 categories checked against Plaid's taxonomy CSV). Plaid's category is what Plaid would
plausibly say, sometimes wrong. Truth lives in a separate `truth.json`. Development (10
businesses) was used for design. Holdout 1 (5) was written after the reviewer was frozen.
Holdouts 2–4 (16) were written by a separate agent that never saw the reviewer, the prompt
or any results.

Cases include payouts that read like transfers, stacked MCAs, NSF fees in many wordings, a
no-fee bank, owner money, hard negatives (`ADVANCE AUTO PARTS`), injections in memos and
61–85 days of history. The engine (`engine/keywords.py`) fails on precedence, punctuation,
`SQUARE` vs `SQUARE CAPITAL` and keywords inside names: 21.7% of groups wrong on development.

## Part 1: the reviewer

Transactions are grouped by direction, counterparty, description shape and engine label.
The model sees each group with amounts and dates, Plaid's category and counterparty type,
and **facts computed by code**: funding followed by fixed repayments, payer matches the
owner, counterparty is a processor, credits that return an earlier debit while the balance
was negative. Bank text is wrapped in `<untrusted>`. The model returns a verdict, a label
(closed enum plus business flag; revenue is derived by code), a confidence, a short reason
and an injection flag. Then code:

1. **Second look**, when the answer contradicts itself (a "flag" that repeats the engine's
   label, because Nova Lite anchors on it) or when structured data supports a label neither
   chose.
2. **Blind review** of groups with payer-written text: asked again with the text *and* the
   engine label removed. If the text changes the credit outcome, an underwriter sees both
   readings. This catches injections by their effect, whatever the wording: 9 of 9 in the
   test sets, one in Spanish.
3. **Policy** (`reviewer/guardrails.py`): a correction is applied only if it is material,
   clears 0.85 confidence when it adds revenue (0.70 otherwise), is not suspicious, and
   **every changed field has a structured signal the model did not write** (Plaid category,
   counterparty type or a code fact). Removing NSF, overdraft or high-risk always goes to a
   person. Otherwise the engine label stays and the flag goes to an underwriter.

**Results (MEASURED against synthetic truth):**

| | Dev | H1 | H2 | H3 | H4 |
|---|---|---|---|---|---|
| Gross revenue error $/mo, engine → reviewer | 148k → **16k** | 17k → **7k** | 48k → **33k** | 55k → **35k** | 39k → **19k** |
| Flag precision / material errors caught | 94% / 96% | 99% / 93% | 91% / 77% | 88% / 90% | 95% / 92% |
| Corrections that made a right label wrong | 0 | 0 | 0 | 0 | 0 |
| Hard negatives sent to an underwriter | 2/89 | 0/14 | 9/66 | 5/55 | 21/110 |

Gross error counts every wrong dollar (net error lets them cancel).

**Measured honestly.** Each blind set was run once before any change, and those runs were
worse: H2 lost a business to a provider failure, H3 had 1 harmful correction, H4 had 8 and
funded a business carrying 4 stacked advances. The fixes are business rules, not cases
(returns detected by structure, lenders don't collect through Zelle, removing distress goes
to a person, repayment burden), and each is neutral or better on the other sets. Before and
after metrics are in `outputs/holdout2/`. What failed: a prompt naming our cases scored
$12k on development because it held the answers; I removed every data-specific name and
started over from $31k. Two prompt rewrites regressed, and an example reason got copied by
the model until I removed it.

**Errors I looked at** (the costliest the reviewer still gets wrong, `reviews.json` against
`truth.json`):
- **Non-sales credits with no clear Plaid category** are the biggest class: a $22,000 child
  care grant (H3, Plaid `TRANSFER_IN_DEPOSIT`), state grants, insurance claims. The model
  calls them revenue or agrees with the engine. False revenue, so the offer goes up.
- **A processor's own financing that looks like its payouts:** $22,000 from Lightspeed (H2)
  arrives with the same descriptor as daily sales, so it sits inside a group of 47 payouts and
  the funding-and-repayment fact (at most 3 lump credits) never fires. $16,000 from Payoneer
  (H3) is repaid by a variable holdback, not fixed debits. False revenue.
- **Owner money through Zelle:** in B03 the "payer matches the owner" fact was shown, but the
  memo said "for payroll" and the model kept it as customer revenue. Plaid backs the engine's
  label, so no second look fired. Nicknames and married names (H3, H1) do not match at all.
- **Plaid evidence that is itself wrong:** Scratchpay pays a vet (H4) for clients who financed
  their bills. Plaid calls it a loan disbursement, so the guardrail let the model move it from
  active_advance to not_revenue. Still wrong, and still not counted as revenue.
- **Held, not wrong:** correct proposals that wait for a person by design (removing a
  garnishment label from Levy Restaurant Supply, a Brightwheel payout at 0.80 confidence). They
  cost underwriter time, not money.

**Model vs code.** The model judges what a counterparty is and whether text is steering it.
Code owns what must be exact or auditable: grouping, facts, revenue, materiality, evidence
and the decision. Nova Lite reports 0.9 confidence for almost everything, so confidence
alone never applies a change. Invalid output is retried once with the errors, then the chunk
is split; provider errors are retried with backoff. Anything unreviewed keeps the engine
label, and the cache stores failures too, so a replay takes the same path.

**Model choice** (final pipeline, five sets):

| | Nova Lite | Claude Haiku 4.5 | Nova Pro |
|---|---|---|---|
| Wrongly funded / harmful corrections | 0 / 0 | 0 / 0 | 0 / 2 |
| Gross revenue error / offer error | $110k / $130k | **$88k** / $131k | $165k / $185k |
| Transactions sent to an underwriter | **188** | 220 | 473 |
| Cost of one run on all five sets | **$0.07** | $1.06 | $0.78 |

Haiku labels better but gives the same offers at 16x the cost, and left 21 transactions
unreviewed after invalid output (that business is referred); Pro sends 2.5x the work.
**Default: Nova Lite on Bedrock**, with the Anthropic API as fallback and `MODEL_ID` to
switch. **Spend: about $2.68 in total**, and `run.py` prints the cached part per model:
Nova Lite $0.11 (the final runs, $0.07, plus earlier runs of the pipeline, blind runs
included, which the cache keeps), Haiku $1.06 and Pro $0.78. The other $0.74 were early
development calls whose cache was deleted along with the overfitted prompt.

## Part 2: credit impact

`credit/features.py` computes from any label set: monthly revenue over the days covered,
revenue share of deposits, NSF and overdraft counts, high-risk share, other funders' daily
payment, and label-free balance signals (negative days, average balance, repayment burden).

On development the brief's rule gives a sum of offer errors of $219k with the engine and
**$8k** with the reviewer, and funds 3 businesses that should get $0 (B04, B07, B08) versus
**0**. B08's bank returns bounced debits instead of charging fees: the engine sees 0 NSFs and
offers $19,885; the reviewer counts 14 returns. B04 has a funder's wire counted as revenue
and its $395 a day not counted as a payment.

**Mislabel simulation** (ESTIMATED, 100 trials, 5% rate, mean offer change when the error
happens):

| Error type | Per transaction | Per counterparty | Flips the decision |
|---|---:|---:|---:|
| Missed NSF | $8,120 | $19,765 | 69% |
| Missed revenue | $2,765 | $13,158 | 1% |
| False revenue | $1,521 | $7,839 | 12% |
| False active advance | $1,494 | $3,224 | 0% |

NSF is a cliff: the rarest error flips the most decisions. Errors per counterparty, which is
how keyword engines fail, cost about 5x more than random ones.

**False revenue vs false advance.** False revenue adds $1.20 to the offer per dollar and puts
principal at risk, often with a business already leveraged. A false advance removes $20 per
daily dollar; that costs margin, not principal. The worst case is a new funder: its funding
counts as revenue *and* its repayments go missing (B04).

**Our decision rule** (`credit/decision.py`, next to the brief's rule). Losses are
asymmetric, so the outcome can be **refer**: decline above 5 NSFs per 90 days; refer under 60
days of history, when negative days exceed 10% of the window, when other funders take more
than 25% of revenue, or when the NSF decision depends on labels in doubt. Nothing is funded
automatically without the cross-check: if the reviewer could not review every transaction
(provider outage, invalid output) or there is no asset report, it refers. The offer uses the
more conservative labels. Across all five sets it wrongly funds and wrongly declines no one.
The brief's rule with the reviewer's labels would still fund U04 and V02 (fees nobody
recognized, but 10 and 11 days negative). The cost: 5 of 36 referred.

**A bank with no NSF fees.** The model never sees an insufficient-funds event, only the fee.
At a no-fee bank the event happens but leaves no text, so zero NSFs means "not measured", not
"healthy". B08 spent 30 of 90 days negative, the worst account in the set, and still gets
$19,885. A model trained on this overfunds those businesses. My fix counts the event, not
the fee: code pairs a credit with an earlier same-amount debit to the same counterparty while the balance was negative,
which found all 37 bounced payments with no false matches, and negative days feed the
decision directly. I would add a per-institution "charges NSF fees" feature so zero is
treated as missing.

**61 days instead of 90.** Sums and counts change meaning. Revenue survives if divided by
the days covered, as ours is; dividing by three understates it by a third. Counts are worse:
5 NSFs in 61 days is about 7.4 over 90, so the applicant looks healthier than it is, and the
model scores out of distribution without failing loudly. Coverage comes from the asset
report and travels with the application, NSFs are compared per 90 days, and under 60 days is
referred. In production I would also monitor coverage and retrain on 90-day histories cut
to shorter windows.

## Part 3: production

**Shadow, then a gate.** The reviewer runs next to the engine and records what it *would*
change. Underwriters label a weekly sample of disagreements and agreements. A correction type
(e.g. processor payout → revenue) goes live only after a fixed window with precision above
a bar, zero harmful corrections and no rise in wrongly funded applications. Types that add
revenue or remove distress need a higher bar or stay human-approved.

**Drift.** Monitor features, not just labels: replay a fixed reference set on every engine,
prompt or model version and compare label mix, revenue share, NSFs, funder payments and offer
(PSI per feature); in production track them by bank and coverage, plus agreement, refer and
override rates. A jump after a release is the alarm, months before outcomes show it.

**Reproducing a decision.** Store the raw Plaid payloads, engine and keyword version, prompt,
model ID and parameters, the cached LLM responses (already keyed by a hash of all inputs),
guardrail and rule versions, features, offer and underwriter actions. Replaying the bundle
gives the original decision; re-running with today's code shows the diff.

**Underwriters.** They see only material flags with reason and evidence, and decide every
refer, distress removal, unsupported revenue addition and injection. Their decisions are
stored per Plaid counterparty entity ID, not by name (`ADVANCE AUTO PARTS` and
`ADVANCE AMERICA`), become evidence for the guardrails and the labeled set for the gate.

## Skipped and known limits

Skipped: real Plaid Sandbox data (the cases had to be planted), RAG (the knowledge fits in
the prompt; an entity corpus would be a keyword list fitted to our data), confidence
calibration, UCC and bureau checks, an underwriter UI. The Anthropic fallback was validated
with the same request body through Bedrock, not with an Anthropic key. Limits: non-sales
credits with no Plaid category (grants, insurance) are often missed; high-risk labels Plaid
can't categorize are never removed automatically; payday lenders become `active_advance`;
all results are on synthetic data, so they show the mechanisms work, not production
accuracy.

## Tools

I used Claude Code as a coding assistant, mainly for:
- **Creating the data.** It wrote the Plaid-format generators from the cases I specified
  (businesses, banks, traps). Holdouts 2–4 were written by a separate Claude agent that was
  told not to open the reviewer, the prompt or any results, so they could be blind tests.
- **Simulations.** It implemented the mislabel Monte Carlo and the before/after offer
  comparison I designed.
- **Comparisons.** It ran the same pipeline on Nova Lite, Claude Haiku 4.5 and Nova Pro and
  tabulated the results.

Also used: Amazon Bedrock, Plaid's API docs and PFC
taxonomy, and public MCA underwriting practice.
