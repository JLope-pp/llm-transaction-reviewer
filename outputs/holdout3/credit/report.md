# Credit impact (reviewer: eu.amazon.nova-lite-v1:0)

## Before / after, per business (MEASURED against synthetic truth)

| Biz | Labels | Monthly rev | Rev % deposits | NSF | OD | High-risk % debits | Other funders $/day | Offer |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| U01 | truth | 24,786 | 69.6% | 11 | 0 | 1.2% | 195 | 0 |
| U01 | engine | 21,147 | 59.3% | 6 | 0 | 0.2% | 0 | 0 |
| U01 | auto | 21,147 | 59.3% | 11 | 0 | 1.2% | 195 | 0 |
| U02 | truth | 37,495 | 72.2% | 11 | 3 | 1.2% | 543 | 0 |
| U02 | engine | 44,861 | 86.4% | 3 | 1 | 1.2% | 0 | 53,833 |
| U02 | auto | 39,539 | 76.1% | 7 | 3 | 1.2% | 543 | 0 |
| U03 | truth | 42,670 | 83.3% | 0 | 0 | 1.7% | 0 | 51,205 |
| U03 | engine | 45,715 | 89.2% | 0 | 0 | 0.0% | 0 | 54,858 |
| U03 | auto | 45,715 | 89.2% | 0 | 0 | 1.0% | 13 | 54,595 |
| U04 | truth | 34,160 | 65.4% | 7 | 3 | 3.9% | 215 | 0 |
| U04 | engine | 38,472 | 73.6% | 4 | 3 | 0.0% | 228 | 41,604 |
| U04 | auto | 38,472 | 73.6% | 4 | 3 | 0.0% | 215 | 41,857 |
| U05 | truth | 83,430 | 85.7% | 0 | 0 | 0.4% | 122 | 97,684 |
| U05 | engine | 89,534 | 92.0% | 0 | 0 | 0.0% | 0 | 107,440 |
| U05 | auto | 84,927 | 87.3% | 0 | 0 | 0.4% | 0 | 101,913 |

| Labels | Abs offer error (sum) | Overstated offers (sum) | Wrong fund/decline decisions |
|---|---:|---:|---|
| engine | $108,846 | $108,846 | 2 ['U02', 'U04'] |
| auto | $49,476 | $49,476 | 1 ['U04'] |
| accept_all | $81,699 | $50,510 | 1 ['U04'] |

## Our rule: fund / decline / refer (reviewer labels + balance + doubt)

| Biz | Decision | Offer | Truth offer (brief's rule) | Reasons |
|---|---|---:|---:|---|
| U01 | decline | 0 | 0 | 11.0 NSFs per 90 days > 5 |
| U02 | decline | 0 | 0 | 7.9 NSFs per 90 days > 5 |
| U03 | fund | 54,594 | 51,205 |  |
| U04 | refer | 41,857 | 0 | 10 negative-balance days with 4 NSFs labeled: the balance shows stress the labels do not explain |
| U05 | fund | 66,495 | 97,684 |  |

Wrongly funded: none. Wrongly declined: none. Overfunded $3,389, underfunded $31,189 (funded only). Referred: ['U04'].

## Mislabel simulation from the true labels (ESTIMATED, Monte Carlo)

Rate = share of the transactions (unit txn) or counterparties (unit counterparty) eligible for that error type. Means per business and trial.

| Unit | Error type | Rate | Offer Δ | |Offer Δ| | Monthly rev Δ | Rev share Δ pp | NSF Δ | High-risk Δ pp | Funders $/day Δ | Decision flips | Hit | |Offer Δ| when hit | Flips when hit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| txn | missed_revenue | 2% | -488 | 488 | -789 | -1.37 | +0.00 | +0.00 | +0 | 0.0% | 59% | 828 | 0.0% |
| txn | missed_revenue | 5% | -1,312 | 1,312 | -2,073 | -3.63 | +0.00 | +0.00 | +0 | 0.0% | 92% | 1,432 | 0.0% |
| txn | missed_revenue | 10% | -2,760 | 2,760 | -4,162 | -7.15 | +0.00 | +0.00 | +0 | 0.0% | 99% | 2,777 | 0.0% |
| txn | false_revenue | 2% | +183 | 183 | +304 | +0.52 | -0.04 | +0.00 | +0 | 0.0% | 13% | 1,430 | 0.0% |
| txn | false_revenue | 5% | +185 | 185 | +588 | +1.12 | -0.14 | +0.00 | +0 | 0.0% | 29% | 630 | 0.0% |
| txn | false_revenue | 10% | +488 | 488 | +1,375 | +2.58 | -0.24 | +0.00 | +0 | 0.0% | 49% | 996 | 0.0% |
| txn | false_advance | 2% | -319 | 319 | +0 | +0.00 | +0.00 | +0.00 | +33 | 0.0% | 86% | 372 | 0.0% |
| txn | false_advance | 5% | -795 | 795 | +0 | +0.00 | +0.00 | +0.00 | +80 | 0.0% | 99% | 802 | 0.0% |
| txn | false_advance | 10% | -2,002 | 2,002 | +0 | +0.00 | +0.00 | +0.00 | +169 | 0.0% | 100% | 2,002 | 0.0% |
| txn | missed_advance | 2% | +8 | 8 | +0 | +0.00 | +0.00 | +0.00 | -4 | 0.0% | 29% | 28 | 0.0% |
| txn | missed_advance | 5% | +25 | 25 | +0 | +0.00 | +0.00 | +0.00 | -11 | 0.0% | 47% | 52 | 0.0% |
| txn | missed_advance | 10% | +43 | 43 | +0 | +0.00 | +0.00 | +0.00 | -21 | 0.0% | 59% | 72 | 0.0% |
| txn | missed_nsf | 2% | +73 | 73 | +37 | +0.09 | -0.11 | +0.00 | +0 | 0.2% | 11% | 692 | 1.9% |
| txn | missed_nsf | 5% | +440 | 440 | +107 | +0.29 | -0.28 | +0.00 | +0 | 1.2% | 22% | 1,983 | 5.4% |
| txn | missed_nsf | 10% | +1,387 | 1,387 | +213 | +0.57 | -0.60 | +0.00 | +0 | 3.8% | 41% | 3,416 | 9.4% |
| txn | false_nsf | 2% | +0 | 0 | +0 | +0.00 | +0.03 | +0.00 | +0 | 0.0% | 3% | 0 | 0.0% |
| txn | false_nsf | 5% | +0 | 0 | +0 | +0.00 | +0.06 | +0.00 | +0 | 0.0% | 5% | 0 | 0.0% |
| txn | false_nsf | 10% | +0 | 0 | +0 | +0.00 | +0.12 | +0.00 | +0 | 0.0% | 11% | 0 | 0.0% |
| txn | immaterial | 2% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 94% | 0 | 0.0% |
| txn | immaterial | 5% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 100% | 0 | 0.0% |
| txn | immaterial | 10% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 100% | 0 | 0.0% |
| txn | uniform | 2% | -578 | 621 | -712 | -1.16 | +0.11 | +0.77 | -2 | 0.0% | 97% | 643 | 0.0% |
| txn | uniform | 5% | -1,370 | 1,864 | -1,941 | -3.10 | +0.39 | +1.84 | -3 | 0.6% | 100% | 1,864 | 0.6% |
| txn | uniform | 10% | -2,020 | 2,772 | -3,355 | -5.74 | +0.78 | +3.55 | -7 | 1.0% | 100% | 2,772 | 1.0% |
| counterparty | missed_revenue | 2% | -695 | 695 | -937 | -1.56 | +0.00 | +0.00 | +0 | 0.0% | 13% | 5,349 | 0.0% |
| counterparty | missed_revenue | 5% | -1,925 | 1,925 | -2,643 | -4.42 | +0.00 | +0.00 | +0 | 0.0% | 27% | 7,077 | 0.0% |
| counterparty | missed_revenue | 10% | -2,782 | 2,782 | -4,584 | -7.80 | +0.00 | +0.00 | +0 | 0.0% | 47% | 5,945 | 0.0% |
| counterparty | false_revenue | 2% | +95 | 95 | +338 | +0.66 | -0.08 | +0.00 | +0 | 0.0% | 13% | 741 | 0.0% |
| counterparty | false_revenue | 5% | +237 | 237 | +527 | +1.04 | -0.15 | +0.00 | +0 | 0.0% | 23% | 1,029 | 0.0% |
| counterparty | false_revenue | 10% | +643 | 643 | +1,279 | +2.35 | -0.25 | +0.00 | +0 | 0.4% | 39% | 1,666 | 1.0% |
| counterparty | false_advance | 2% | -253 | 253 | +0 | +0.00 | +0.00 | +0.00 | +27 | 0.0% | 23% | 1,082 | 0.0% |
| counterparty | false_advance | 5% | -745 | 745 | +0 | +0.00 | +0.00 | +0.00 | +77 | 0.0% | 43% | 1,741 | 0.0% |
| counterparty | false_advance | 10% | -2,167 | 2,167 | +0 | +0.00 | +0.00 | +0.00 | +167 | 0.0% | 67% | 3,244 | 0.0% |
| counterparty | missed_advance | 2% | +15 | 15 | +0 | +0.00 | +0.00 | +0.00 | -9 | 0.0% | 3% | 456 | 0.0% |
| counterparty | missed_advance | 5% | +29 | 29 | +0 | +0.00 | +0.00 | +0.00 | -10 | 0.0% | 5% | 635 | 0.0% |
| counterparty | missed_advance | 10% | +73 | 73 | +0 | +0.00 | +0.00 | +0.00 | -23 | 0.0% | 11% | 676 | 0.0% |
| counterparty | missed_nsf | 2% | +734 | 734 | +75 | +0.20 | -0.15 | +0.00 | +0 | 2.0% | 7% | 11,116 | 30.3% |
| counterparty | missed_nsf | 5% | +1,242 | 1,242 | +79 | +0.21 | -0.29 | +0.00 | +0 | 3.4% | 13% | 9,270 | 25.4% |
| counterparty | missed_nsf | 10% | +1,968 | 1,968 | +176 | +0.48 | -0.50 | +0.00 | +0 | 5.4% | 20% | 10,042 | 27.6% |
| counterparty | false_nsf | 2% | +0 | 0 | +0 | +0.00 | +0.01 | +0.00 | +0 | 0.0% | 1% | 0 | 0.0% |
| counterparty | false_nsf | 5% | +0 | 0 | +0 | +0.00 | +0.05 | +0.00 | +0 | 0.0% | 3% | 0 | 0.0% |
| counterparty | false_nsf | 10% | +0 | 0 | +0 | +0.00 | +0.12 | +0.00 | +0 | 0.0% | 7% | 0 | 0.0% |
| counterparty | immaterial | 2% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 29% | 0 | 0.0% |
| counterparty | immaterial | 5% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 57% | 0 | 0.0% |
| counterparty | immaterial | 10% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 82% | 0 | 0.0% |
| counterparty | uniform | 2% | +170 | 984 | -669 | -1.20 | +0.19 | +0.78 | -4 | 1.6% | 41% | 2,377 | 3.9% |
| counterparty | uniform | 5% | -867 | 2,547 | -1,764 | -2.99 | +0.37 | +2.25 | -6 | 2.6% | 78% | 3,282 | 3.4% |
| counterparty | uniform | 10% | -1,246 | 4,532 | -3,630 | -6.20 | +0.80 | +3.52 | -14 | 5.0% | 94% | 4,822 | 5.3% |
