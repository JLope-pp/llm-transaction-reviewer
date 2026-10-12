# Credit impact (reviewer: eu.amazon.nova-lite-v1:0)

## Before / after, per business (MEASURED against synthetic truth)

| Biz | Labels | Monthly rev | Rev % deposits | NSF | OD | High-risk % debits | Other funders $/day | Offer |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| H01 | truth | 97,004 | 87.8% | 0 | 0 | 0.0% | 615 | 104,105 |
| H01 | engine | 97,004 | 87.8% | 0 | 0 | 0.0% | 214 | 112,125 |
| H01 | auto | 97,004 | 87.8% | 0 | 0 | 0.0% | 615 | 104,105 |
| H02 | truth | 60,590 | 90.9% | 0 | 0 | 0.0% | 240 | 67,908 |
| H02 | engine | 66,670 | 100.0% | 0 | 0 | 0.0% | 0 | 80,004 |
| H02 | auto | 60,590 | 90.9% | 0 | 0 | 0.0% | 240 | 67,908 |
| H03 | truth | 22,883 | 91.0% | 0 | 0 | 5.9% | 0 | 27,460 |
| H03 | engine | 24,910 | 99.0% | 0 | 0 | 0.5% | 0 | 29,892 |
| H03 | auto | 24,910 | 99.0% | 0 | 0 | 5.9% | 0 | 29,892 |
| H04 | truth | 31,420 | 100.0% | 5 | 2 | 1.5% | 419 | 29,322 |
| H04 | engine | 29,123 | 92.7% | 2 | 2 | 1.5% | 210 | 30,748 |
| H04 | auto | 29,123 | 92.7% | 5 | 2 | 1.5% | 210 | 30,748 |
| H05 | truth | 21,265 | 74.1% | 4 | 0 | 0.0% | 365 | 18,218 |
| H05 | engine | 19,472 | 67.9% | 0 | 0 | 0.0% | 0 | 23,366 |
| H05 | auto | 23,799 | 83.0% | 4 | 0 | 0.0% | 365 | 21,258 |

| Labels | Abs offer error (sum) | Overstated offers (sum) | Wrong fund/decline decisions |
|---|---:|---:|---|
| engine | $29,122 | $29,122 | 0 [] |
| auto | $6,898 | $6,898 | 0 [] |
| accept_all | $25,080 | $6,898 | 0 [] |

## Our rule: fund / decline / refer (reviewer labels + balance + doubt)

| Biz | Decision | Offer | Truth offer (brief's rule) | Reasons |
|---|---|---:|---:|---|
| H01 | fund | 85,923 | 104,105 |  |
| H02 | fund | 67,908 | 67,908 |  |
| H03 | fund | 29,892 | 27,460 |  |
| H04 | refer | 30,748 | 29,322 | 42 negative-balance days with 5 NSFs labeled: the balance shows stress the labels do not explain |
| H05 | refer | 21,259 | 18,218 | 13 negative-balance days with 4 NSFs labeled: the balance shows stress the labels do not explain; other funders already take 33% of monthly revenue |

Wrongly funded: none. Wrongly declined: none. Overfunded $2,432, underfunded $18,182 (funded only). Referred: ['H04', 'H05'].

## Mislabel simulation from the true labels (ESTIMATED, Monte Carlo)

Rate = share of the transactions (unit txn) or counterparties (unit counterparty) eligible for that error type. Means per business and trial.

| Unit | Error type | Rate | Offer Δ | |Offer Δ| | Monthly rev Δ | Rev share Δ pp | NSF Δ | High-risk Δ pp | Funders $/day Δ | Decision flips | Hit | |Offer Δ| when hit | Flips when hit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| txn | missed_revenue | 2% | -1,030 | 1,030 | -858 | -1.66 | +0.00 | +0.00 | +0 | 0.0% | 68% | 1,505 | 0.0% |
| txn | missed_revenue | 5% | -2,947 | 2,947 | -2,456 | -4.66 | +0.00 | +0.00 | +0 | 0.0% | 95% | 3,108 | 0.0% |
| txn | missed_revenue | 10% | -5,456 | 5,456 | -4,547 | -8.70 | +0.00 | +0.00 | +0 | 0.0% | 99% | 5,489 | 0.0% |
| txn | false_revenue | 2% | +55 | 55 | +46 | +0.14 | -0.02 | +0.00 | +0 | 0.0% | 4% | 1,376 | 0.0% |
| txn | false_revenue | 5% | +396 | 396 | +330 | +0.58 | -0.04 | +0.00 | +0 | 0.0% | 12% | 3,303 | 0.0% |
| txn | false_revenue | 10% | +786 | 786 | +655 | +1.13 | -0.07 | +0.00 | +0 | 0.0% | 22% | 3,572 | 0.0% |
| txn | false_advance | 2% | -738 | 738 | +0 | +0.00 | +0.00 | +0.00 | +37 | 0.0% | 82% | 898 | 0.0% |
| txn | false_advance | 5% | -1,795 | 1,795 | +0 | +0.00 | +0.00 | +0.00 | +90 | 0.0% | 98% | 1,835 | 0.0% |
| txn | false_advance | 10% | -3,189 | 3,189 | +0 | +0.00 | +0.00 | +0.00 | +159 | 0.0% | 100% | 3,189 | 0.0% |
| txn | missed_advance | 2% | +154 | 154 | +0 | +0.00 | +0.00 | +0.00 | -8 | 0.0% | 57% | 272 | 0.0% |
| txn | missed_advance | 5% | +326 | 326 | +0 | +0.00 | +0.00 | +0.00 | -16 | 0.0% | 75% | 436 | 0.0% |
| txn | missed_advance | 10% | +639 | 639 | +0 | +0.00 | +0.00 | +0.00 | -32 | 0.0% | 79% | 807 | 0.0% |
| txn | missed_nsf | 2% | +3 | 3 | +2 | +0.01 | -0.04 | +0.00 | +0 | 0.0% | 3% | 78 | 0.0% |
| txn | missed_nsf | 5% | +7 | 7 | +6 | +0.02 | -0.08 | +0.00 | +0 | 0.0% | 7% | 95 | 0.0% |
| txn | missed_nsf | 10% | +14 | 14 | +12 | +0.05 | -0.20 | +0.00 | +0 | 0.0% | 17% | 81 | 0.0% |
| txn | false_nsf | 2% | -117 | 117 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.4% | 0% | 29,322 | 100.0% |
| txn | false_nsf | 5% | -586 | 586 | +0 | +0.00 | +0.02 | +0.00 | +0 | 2.0% | 2% | 29,322 | 100.0% |
| txn | false_nsf | 10% | -1,114 | 1,114 | +0 | +0.00 | +0.04 | +0.00 | +0 | 3.8% | 4% | 29,322 | 100.0% |
| txn | immaterial | 2% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 95% | 0 | 0.0% |
| txn | immaterial | 5% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 100% | 0 | 0.0% |
| txn | immaterial | 10% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 100% | 0 | 0.0% |
| txn | uniform | 2% | -2,168 | 2,275 | -816 | -1.55 | +0.24 | +0.83 | -3 | 4.4% | 99% | 2,308 | 4.5% |
| txn | uniform | 5% | -5,199 | 5,346 | -1,781 | -3.45 | +0.66 | +1.86 | -10 | 12.6% | 100% | 5,346 | 12.6% |
| txn | uniform | 10% | -8,675 | 8,923 | -3,543 | -6.89 | +1.30 | +3.72 | -22 | 18.8% | 100% | 8,923 | 18.8% |
| counterparty | missed_revenue | 2% | -1,506 | 1,506 | -1,274 | -2.23 | +0.00 | +0.00 | +0 | 1.0% | 8% | 17,933 | 11.9% |
| counterparty | missed_revenue | 5% | -2,675 | 2,675 | -2,289 | -4.66 | +0.00 | +0.00 | +0 | 2.4% | 19% | 13,932 | 12.5% |
| counterparty | missed_revenue | 10% | -5,837 | 5,837 | -4,976 | -9.56 | +0.00 | +0.00 | +0 | 4.2% | 36% | 16,397 | 11.8% |
| counterparty | false_revenue | 2% | +212 | 212 | +176 | +0.32 | -0.02 | +0.00 | +0 | 0.0% | 5% | 4,603 | 0.0% |
| counterparty | false_revenue | 5% | +330 | 330 | +275 | +0.52 | -0.06 | +0.00 | +0 | 0.0% | 7% | 4,998 | 0.0% |
| counterparty | false_revenue | 10% | +652 | 652 | +543 | +1.07 | -0.08 | +0.00 | +0 | 0.0% | 14% | 4,592 | 0.0% |
| counterparty | false_advance | 2% | -587 | 587 | +0 | +0.00 | +0.00 | +0.00 | +29 | 0.0% | 26% | 2,258 | 0.0% |
| counterparty | false_advance | 5% | -1,951 | 1,951 | +0 | +0.00 | +0.00 | +0.00 | +98 | 0.0% | 48% | 4,083 | 0.0% |
| counterparty | false_advance | 10% | -3,294 | 3,294 | +0 | +0.00 | +0.00 | +0.00 | +165 | 0.0% | 75% | 4,380 | 0.0% |
| counterparty | missed_advance | 2% | +186 | 186 | +0 | +0.00 | +0.00 | +0.00 | -9 | 0.0% | 3% | 5,828 | 0.0% |
| counterparty | missed_advance | 5% | +299 | 299 | +0 | +0.00 | +0.00 | +0.00 | -15 | 0.0% | 5% | 6,491 | 0.0% |
| counterparty | missed_advance | 10% | +753 | 753 | +0 | +0.00 | +0.00 | +0.00 | -38 | 0.0% | 11% | 6,847 | 0.0% |
| counterparty | missed_nsf | 2% | +1 | 1 | +1 | +0.00 | -0.02 | +0.00 | +0 | 0.0% | 1% | 118 | 0.0% |
| counterparty | missed_nsf | 5% | +14 | 14 | +12 | +0.04 | -0.16 | +0.00 | +0 | 0.0% | 6% | 237 | 0.0% |
| counterparty | missed_nsf | 10% | +7 | 7 | +6 | +0.02 | -0.14 | +0.00 | +0 | 0.0% | 6% | 115 | 0.0% |
| counterparty | false_nsf | 2% | -117 | 117 | +0 | +0.00 | +0.01 | +0.00 | +0 | 0.4% | 0% | 29,322 | 100.0% |
| counterparty | false_nsf | 5% | -176 | 176 | +0 | +0.00 | +0.01 | +0.00 | +0 | 0.6% | 1% | 29,322 | 100.0% |
| counterparty | false_nsf | 10% | -704 | 704 | +0 | +0.00 | +0.05 | +0.00 | +0 | 2.4% | 2% | 29,322 | 100.0% |
| counterparty | immaterial | 2% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 30% | 0 | 0.0% |
| counterparty | immaterial | 5% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 60% | 0 | 0.0% |
| counterparty | immaterial | 10% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 84% | 0 | 0.0% |
| counterparty | uniform | 2% | -1,103 | 1,425 | -587 | -0.99 | +0.20 | +0.73 | -4 | 1.8% | 34% | 4,242 | 5.4% |
| counterparty | uniform | 5% | -5,173 | 5,435 | -2,199 | -4.41 | +0.75 | +1.68 | -9 | 11.2% | 66% | 8,210 | 16.9% |
| counterparty | uniform | 10% | -7,982 | 8,320 | -2,838 | -4.91 | +1.21 | +3.59 | -19 | 17.2% | 87% | 9,520 | 19.7% |
