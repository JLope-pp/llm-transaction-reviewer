# Credit impact (reviewer: eu.amazon.nova-lite-v1:0)

## Before / after, per business (MEASURED against synthetic truth)

| Biz | Labels | Monthly rev | Rev % deposits | NSF | OD | High-risk % debits | Other funders $/day | Offer |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| T01 | truth | 60,172 | 81.0% | 0 | 0 | 0.0% | 412 | 63,957 |
| T01 | engine | 67,740 | 91.2% | 0 | 0 | 0.0% | 0 | 81,289 |
| T01 | auto | 56,932 | 76.6% | 0 | 0 | 0.0% | 412 | 60,068 |
| T02 | truth | 64,979 | 68.9% | 0 | 0 | 0.0% | 209 | 73,793 |
| T02 | engine | 67,107 | 71.1% | 0 | 0 | 0.0% | 0 | 80,528 |
| T02 | auto | 71,306 | 75.6% | 0 | 0 | 0.0% | 0 | 85,567 |
| T03 | truth | 24,365 | 70.4% | 10 | 4 | 6.3% | 587 | 0 |
| T03 | engine | 31,597 | 91.3% | 5 | 3 | 1.9% | 188 | 34,163 |
| T03 | auto | 31,597 | 91.3% | 6 | 4 | 1.9% | 349 | 0 |
| T04 | truth | 9,694 | 52.8% | 6 | 0 | 24.0% | 181 | 0 |
| T04 | engine | 10,722 | 58.4% | 4 | 0 | 13.7% | 0 | 12,867 |
| T04 | auto | 10,722 | 58.4% | 6 | 0 | 22.7% | 196 | 0 |
| T05 | truth | 64,263 | 89.5% | 0 | 0 | 0.7% | 0 | 77,116 |
| T05 | engine | 66,784 | 93.0% | 0 | 0 | 0.7% | 0 | 80,141 |
| T05 | auto | 66,784 | 93.0% | 0 | 0 | 0.7% | 0 | 80,141 |

| Labels | Abs offer error (sum) | Overstated offers (sum) | Wrong fund/decline decisions |
|---|---:|---:|---|
| engine | $74,122 | $74,122 | 2 ['T03', 'T04'] |
| auto | $18,688 | $14,799 | 0 [] |
| accept_all | $17,611 | $17,611 | 1 ['T04'] |

## Our rule: fund / decline / refer (reviewer labels + balance + doubt)

| Biz | Decision | Offer | Truth offer (brief's rule) | Reasons |
|---|---|---:|---:|---|
| T01 | fund | 60,068 | 63,957 |  |
| T02 | fund | 75,931 | 73,793 |  |
| T03 | decline | 0 | 0 | 6.0 NSFs per 90 days > 5 |
| T04 | decline | 0 | 0 | 8.4 NSFs per 90 days > 5 |
| T05 | fund | 80,141 | 77,116 |  |

Wrongly funded: none. Wrongly declined: none. Overfunded $5,163, underfunded $3,889 (funded only). Referred: none.

## Mislabel simulation from the true labels (ESTIMATED, Monte Carlo)

Rate = share of the transactions (unit txn) or counterparties (unit counterparty) eligible for that error type. Means per business and trial.

| Unit | Error type | Rate | Offer Δ | |Offer Δ| | Monthly rev Δ | Rev share Δ pp | NSF Δ | High-risk Δ pp | Funders $/day Δ | Decision flips | Hit | |Offer Δ| when hit | Flips when hit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| txn | missed_revenue | 2% | -935 | 935 | -906 | -1.43 | +0.00 | +0.00 | +0 | 0.0% | 73% | 1,284 | 0.0% |
| txn | missed_revenue | 5% | -2,407 | 2,407 | -2,337 | -3.73 | +0.00 | +0.00 | +0 | 0.0% | 95% | 2,523 | 0.0% |
| txn | missed_revenue | 10% | -4,349 | 4,349 | -4,330 | -7.08 | +0.00 | +0.00 | +0 | 0.0% | 100% | 4,349 | 0.0% |
| txn | false_revenue | 2% | +595 | 595 | +398 | +0.64 | -0.02 | +0.00 | +0 | 2.2% | 12% | 5,129 | 19.0% |
| txn | false_revenue | 5% | +987 | 987 | +649 | +1.18 | -0.05 | +0.00 | +0 | 4.2% | 26% | 3,737 | 15.9% |
| txn | false_revenue | 10% | +2,003 | 2,003 | +1,363 | +2.60 | -0.11 | +0.00 | +0 | 8.2% | 47% | 4,262 | 17.4% |
| txn | false_advance | 2% | -558 | 558 | +0 | +0.00 | +0.00 | +0.00 | +33 | 0.0% | 79% | 703 | 0.0% |
| txn | false_advance | 5% | -1,348 | 1,348 | +0 | +0.00 | +0.00 | +0.00 | +81 | 0.0% | 97% | 1,390 | 0.0% |
| txn | false_advance | 10% | -2,813 | 2,813 | +0 | +0.00 | +0.00 | +0.00 | +167 | 0.0% | 100% | 2,813 | 0.0% |
| txn | missed_advance | 2% | +63 | 63 | +0 | +0.00 | +0.00 | +0.00 | -6 | 0.0% | 38% | 166 | 0.0% |
| txn | missed_advance | 5% | +135 | 135 | +0 | +0.00 | +0.00 | +0.00 | -15 | 0.0% | 55% | 247 | 0.0% |
| txn | missed_advance | 10% | +235 | 235 | +0 | +0.00 | +0.00 | +0.00 | -26 | 0.0% | 66% | 355 | 0.0% |
| txn | missed_nsf | 2% | +166 | 166 | +5 | +0.03 | -0.06 | +0.00 | +0 | 2.0% | 6% | 2,966 | 35.7% |
| txn | missed_nsf | 5% | +435 | 435 | +15 | +0.08 | -0.17 | +0.00 | +0 | 5.2% | 13% | 3,293 | 39.4% |
| txn | missed_nsf | 10% | +887 | 887 | +28 | +0.15 | -0.34 | +0.00 | +0 | 10.4% | 25% | 3,604 | 42.3% |
| txn | false_nsf | 2% | +0 | 0 | +0 | +0.00 | +0.01 | +0.00 | +0 | 0.0% | 1% | 0 | 0.0% |
| txn | false_nsf | 5% | +0 | 0 | +0 | +0.00 | +0.04 | +0.00 | +0 | 0.0% | 3% | 0 | 0.0% |
| txn | false_nsf | 10% | +0 | 0 | +0 | +0.00 | +0.08 | +0.00 | +0 | 0.0% | 7% | 0 | 0.0% |
| txn | immaterial | 2% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 94% | 0 | 0.0% |
| txn | immaterial | 5% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 100% | 0 | 0.0% |
| txn | immaterial | 10% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 100% | 0 | 0.0% |
| txn | uniform | 2% | -662 | 1,054 | -720 | -1.13 | +0.25 | +0.57 | -1 | 1.4% | 97% | 1,087 | 1.4% |
| txn | uniform | 5% | -1,511 | 2,084 | -1,658 | -2.61 | +0.57 | +1.59 | -6 | 2.6% | 100% | 2,084 | 2.6% |
| txn | uniform | 10% | -3,287 | 3,848 | -3,382 | -5.46 | +1.21 | +3.42 | -8 | 3.0% | 100% | 3,848 | 3.0% |
| counterparty | missed_revenue | 2% | -1,031 | 1,031 | -982 | -1.54 | +0.00 | +0.00 | +0 | 0.0% | 12% | 8,885 | 0.0% |
| counterparty | missed_revenue | 5% | -1,867 | 1,867 | -1,791 | -2.83 | +0.00 | +0.00 | +0 | 0.0% | 24% | 7,781 | 0.0% |
| counterparty | missed_revenue | 10% | -4,530 | 4,530 | -4,673 | -7.97 | +0.00 | +0.00 | +0 | 0.0% | 43% | 10,584 | 0.0% |
| counterparty | false_revenue | 2% | +421 | 421 | +453 | +0.99 | -0.02 | +0.00 | +0 | 0.8% | 12% | 3,399 | 6.5% |
| counterparty | false_revenue | 5% | +724 | 724 | +461 | +0.84 | -0.05 | +0.00 | +0 | 3.6% | 19% | 3,733 | 18.6% |
| counterparty | false_revenue | 10% | +1,701 | 1,701 | +1,321 | +2.67 | -0.10 | +0.00 | +0 | 5.6% | 35% | 4,804 | 15.8% |
| counterparty | false_advance | 2% | -693 | 693 | +0 | +0.00 | +0.00 | +0.00 | +40 | 0.0% | 26% | 2,687 | 0.0% |
| counterparty | false_advance | 5% | -1,460 | 1,460 | +0 | +0.00 | +0.00 | +0.00 | +85 | 0.0% | 47% | 3,120 | 0.0% |
| counterparty | false_advance | 10% | -2,786 | 2,786 | +0 | +0.00 | +0.00 | +0.00 | +162 | 0.0% | 74% | 3,764 | 0.0% |
| counterparty | missed_advance | 2% | +41 | 41 | +0 | +0.00 | +0.00 | +0.00 | -9 | 0.0% | 3% | 1,293 | 0.0% |
| counterparty | missed_advance | 5% | +91 | 91 | +0 | +0.00 | +0.00 | +0.00 | -13 | 0.0% | 5% | 1,980 | 0.0% |
| counterparty | missed_advance | 10% | +265 | 265 | +0 | +0.00 | +0.00 | +0.00 | -31 | 0.0% | 11% | 2,410 | 0.0% |
| counterparty | missed_nsf | 2% | +171 | 171 | +9 | +0.05 | -0.06 | +0.00 | +0 | 2.0% | 3% | 5,690 | 66.7% |
| counterparty | missed_nsf | 5% | +372 | 372 | +14 | +0.07 | -0.20 | +0.00 | +0 | 4.2% | 9% | 4,043 | 45.7% |
| counterparty | missed_nsf | 10% | +769 | 769 | +22 | +0.12 | -0.33 | +0.00 | +0 | 7.6% | 12% | 6,199 | 61.3% |
| counterparty | false_nsf | 2% | +0 | 0 | +0 | +0.00 | +0.01 | +0.00 | +0 | 0.0% | 1% | 0 | 0.0% |
| counterparty | false_nsf | 5% | +0 | 0 | +0 | +0.00 | +0.02 | +0.00 | +0 | 0.0% | 1% | 0 | 0.0% |
| counterparty | false_nsf | 10% | +0 | 0 | +0 | +0.00 | +0.07 | +0.00 | +0 | 0.0% | 3% | 0 | 0.0% |
| counterparty | immaterial | 2% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 33% | 0 | 0.0% |
| counterparty | immaterial | 5% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 62% | 0 | 0.0% |
| counterparty | immaterial | 10% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 84% | 0 | 0.0% |
| counterparty | uniform | 2% | -730 | 1,313 | -659 | -1.06 | +0.22 | +0.64 | -3 | 1.6% | 43% | 3,068 | 3.7% |
| counterparty | uniform | 5% | -2,257 | 3,345 | -1,886 | -2.97 | +0.59 | +1.82 | -1 | 4.8% | 77% | 4,321 | 6.2% |
| counterparty | uniform | 10% | -3,883 | 5,467 | -3,156 | -4.94 | +0.99 | +3.29 | -8 | 6.2% | 94% | 5,791 | 6.6% |
