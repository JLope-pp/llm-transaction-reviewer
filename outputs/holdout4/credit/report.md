# Credit impact (reviewer: eu.amazon.nova-lite-v1:0)

## Before / after, per business (MEASURED against synthetic truth)

| Biz | Labels | Monthly rev | Rev % deposits | NSF | OD | High-risk % debits | Other funders $/day | Offer |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| V01 | truth | 24,605 | 55.2% | 14 | 0 | 1.5% | 785 | 0 |
| V01 | engine | 30,336 | 68.1% | 6 | 0 | 0.3% | 785 | 0 |
| V01 | auto | 24,875 | 55.8% | 15 | 0 | 0.3% | 785 | 0 |
| V02 | truth | 36,482 | 73.3% | 8 | 3 | 1.5% | 422 | 0 |
| V02 | engine | 42,697 | 85.8% | 0 | 0 | 0.0% | 0 | 51,236 |
| V02 | auto | 37,664 | 75.6% | 2 | 0 | 1.5% | 422 | 36,760 |
| V03 | truth | 36,913 | 65.7% | 0 | 0 | 1.6% | 1,129 | 21,723 |
| V03 | engine | 47,215 | 84.1% | 0 | 0 | 1.6% | 380 | 49,058 |
| V03 | auto | 37,926 | 67.5% | 0 | 0 | 1.6% | 1,129 | 22,939 |
| V04 | truth | 23,023 | 72.4% | 3 | 1 | 0.9% | 138 | 24,865 |
| V04 | engine | 25,398 | 79.8% | 3 | 1 | 0.0% | 0 | 30,478 |
| V04 | auto | 25,398 | 79.8% | 3 | 1 | 0.0% | 138 | 27,715 |
| V05 | truth | 59,101 | 72.4% | 2 | 1 | 0.0% | 0 | 70,922 |
| V05 | engine | 56,568 | 69.3% | 2 | 1 | 0.0% | 0 | 67,882 |
| V05 | auto | 56,568 | 69.3% | 2 | 1 | 0.0% | 0 | 67,882 |
| V06 | truth | 82,229 | 96.9% | 0 | 0 | 0.0% | 0 | 98,675 |
| V06 | engine | 79,896 | 94.1% | 0 | 0 | 0.0% | 0 | 95,875 |
| V06 | auto | 79,896 | 94.1% | 0 | 0 | 0.0% | 0 | 95,875 |

| Labels | Abs offer error (sum) | Overstated offers (sum) | Wrong fund/decline decisions |
|---|---:|---:|---|
| engine | $90,024 | $84,184 | 1 ['V02'] |
| auto | $46,666 | $40,826 | 1 ['V02'] |
| accept_all | $46,181 | $40,862 | 1 ['V02'] |

## Our rule: fund / decline / refer (reviewer labels + balance + doubt)

| Biz | Decision | Offer | Truth offer (brief's rule) | Reasons |
|---|---|---:|---:|---|
| V01 | decline | 0 | 0 | 15.0 NSFs per 90 days > 5 |
| V02 | refer | 36,760 | 0 | 11 negative-balance days with 2 NSFs labeled: the balance shows stress the labels do not explain |
| V03 | refer | 22,938 | 21,723 | other funders already take 65% of monthly revenue |
| V04 | fund | 27,714 | 24,865 |  |
| V05 | fund | 67,882 | 70,922 |  |
| V06 | fund | 95,875 | 98,675 |  |

Wrongly funded: none. Wrongly declined: none. Overfunded $2,849, underfunded $5,840 (funded only). Referred: ['V02', 'V03'].

## Mislabel simulation from the true labels (ESTIMATED, Monte Carlo)

Rate = share of the transactions (unit txn) or counterparties (unit counterparty) eligible for that error type. Means per business and trial.

| Unit | Error type | Rate | Offer Δ | |Offer Δ| | Monthly rev Δ | Rev share Δ pp | NSF Δ | High-risk Δ pp | Funders $/day Δ | Decision flips | Hit | |Offer Δ| when hit | Flips when hit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| txn | missed_revenue | 2% | -821 | 821 | -889 | -1.48 | +0.00 | +0.00 | +0 | 0.0% | 72% | 1,136 | 0.0% |
| txn | missed_revenue | 5% | -2,160 | 2,160 | -2,333 | -3.87 | +0.00 | +0.00 | +0 | 0.0% | 98% | 2,197 | 0.0% |
| txn | missed_revenue | 10% | -3,944 | 3,944 | -4,291 | -7.14 | +0.00 | +0.00 | +0 | 0.0% | 100% | 3,944 | 0.0% |
| txn | false_revenue | 2% | +253 | 253 | +305 | +0.54 | -0.04 | +0.00 | +0 | 0.0% | 11% | 2,301 | 0.0% |
| txn | false_revenue | 5% | +457 | 457 | +729 | +1.43 | -0.10 | +0.00 | +0 | 0.0% | 25% | 1,804 | 0.0% |
| txn | false_revenue | 10% | +1,022 | 1,022 | +1,463 | +2.69 | -0.21 | +0.00 | +0 | 0.0% | 42% | 2,405 | 0.0% |
| txn | false_advance | 2% | -491 | 491 | +0 | +0.00 | +0.00 | +0.00 | +32 | 0.0% | 77% | 636 | 0.0% |
| txn | false_advance | 5% | -1,162 | 1,162 | +0 | +0.00 | +0.00 | +0.00 | +80 | 0.0% | 96% | 1,208 | 0.0% |
| txn | false_advance | 10% | -2,429 | 2,429 | +0 | +0.00 | +0.00 | +0.00 | +165 | 0.0% | 100% | 2,429 | 0.0% |
| txn | missed_advance | 2% | +80 | 80 | +0 | +0.00 | +0.00 | +0.00 | -8 | 0.0% | 48% | 167 | 0.0% |
| txn | missed_advance | 5% | +252 | 252 | +0 | +0.00 | +0.00 | +0.00 | -22 | 0.0% | 56% | 453 | 0.0% |
| txn | missed_advance | 10% | +399 | 399 | +0 | +0.00 | +0.00 | +0.00 | -40 | 0.0% | 58% | 681 | 0.0% |
| txn | missed_nsf | 2% | +0 | 0 | +54 | +0.12 | -0.09 | +0.00 | +0 | 0.0% | 8% | 0 | 0.0% |
| txn | missed_nsf | 5% | +59 | 59 | +113 | +0.25 | -0.23 | +0.00 | +0 | 0.2% | 17% | 340 | 1.0% |
| txn | missed_nsf | 10% | +118 | 118 | +224 | +0.51 | -0.47 | +0.00 | +0 | 0.3% | 30% | 386 | 1.1% |
| txn | false_nsf | 2% | +0 | 0 | +0 | +0.00 | +0.02 | +0.00 | +0 | 0.0% | 2% | 0 | 0.0% |
| txn | false_nsf | 5% | +0 | 0 | +0 | +0.00 | +0.04 | +0.00 | +0 | 0.0% | 4% | 0 | 0.0% |
| txn | false_nsf | 10% | +0 | 0 | +0 | +0.00 | +0.08 | +0.00 | +0 | 0.0% | 8% | 0 | 0.0% |
| txn | immaterial | 2% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 94% | 0 | 0.0% |
| txn | immaterial | 5% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 100% | 0 | 0.0% |
| txn | immaterial | 10% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 100% | 0 | 0.0% |
| txn | uniform | 2% | -576 | 730 | -668 | -1.11 | +0.25 | +0.70 | -7 | 0.0% | 99% | 736 | 0.0% |
| txn | uniform | 5% | -1,774 | 2,095 | -1,655 | -2.72 | +0.61 | +1.81 | -14 | 0.7% | 100% | 2,095 | 0.7% |
| txn | uniform | 10% | -4,436 | 4,942 | -3,344 | -5.54 | +1.18 | +3.73 | -26 | 3.5% | 100% | 4,942 | 3.5% |
| counterparty | missed_revenue | 2% | -768 | 768 | -868 | -1.40 | +0.00 | +0.00 | +0 | 0.5% | 11% | 6,779 | 4.4% |
| counterparty | missed_revenue | 5% | -1,614 | 1,614 | -1,909 | -3.05 | +0.00 | +0.00 | +0 | 0.7% | 25% | 6,545 | 2.7% |
| counterparty | missed_revenue | 10% | -3,432 | 3,432 | -3,945 | -6.74 | +0.00 | +0.00 | +0 | 1.5% | 43% | 8,044 | 3.5% |
| counterparty | false_revenue | 2% | +289 | 289 | +405 | +0.71 | -0.05 | +0.00 | +0 | 0.0% | 11% | 2,630 | 0.0% |
| counterparty | false_revenue | 5% | +694 | 694 | +763 | +1.45 | -0.14 | +0.00 | +0 | 0.3% | 20% | 3,472 | 1.7% |
| counterparty | false_revenue | 10% | +1,054 | 1,054 | +1,357 | +2.58 | -0.20 | +0.00 | +0 | 0.0% | 34% | 3,131 | 0.0% |
| counterparty | false_advance | 2% | -423 | 423 | +0 | +0.00 | +0.00 | +0.00 | +33 | 0.0% | 19% | 2,264 | 0.0% |
| counterparty | false_advance | 5% | -1,076 | 1,076 | +0 | +0.00 | +0.00 | +0.00 | +82 | 0.0% | 36% | 2,962 | 0.0% |
| counterparty | false_advance | 10% | -2,636 | 2,636 | +0 | +0.00 | +0.00 | +0.00 | +181 | 0.0% | 59% | 4,480 | 0.0% |
| counterparty | missed_advance | 2% | +140 | 140 | +0 | +0.00 | +0.00 | +0.00 | -11 | 0.0% | 4% | 3,807 | 0.0% |
| counterparty | missed_advance | 5% | +181 | 181 | +0 | +0.00 | +0.00 | +0.00 | -16 | 0.0% | 6% | 3,106 | 0.0% |
| counterparty | missed_advance | 10% | +519 | 519 | +0 | +0.00 | +0.00 | +0.00 | -46 | 0.0% | 16% | 3,349 | 0.0% |
| counterparty | missed_nsf | 2% | +177 | 177 | +34 | +0.08 | -0.10 | +0.00 | +0 | 0.5% | 4% | 3,927 | 11.1% |
| counterparty | missed_nsf | 5% | +471 | 471 | +132 | +0.30 | -0.26 | +0.00 | +0 | 1.3% | 9% | 5,049 | 14.3% |
| counterparty | missed_nsf | 10% | +827 | 827 | +261 | +0.59 | -0.43 | +0.00 | +0 | 2.5% | 14% | 6,122 | 18.5% |
| counterparty | false_nsf | 2% | +0 | 0 | +0 | +0.00 | +0.01 | +0.00 | +0 | 0.0% | 1% | 0 | 0.0% |
| counterparty | false_nsf | 5% | +0 | 0 | +0 | +0.00 | +0.03 | +0.00 | +0 | 0.0% | 2% | 0 | 0.0% |
| counterparty | false_nsf | 10% | +0 | 0 | +0 | +0.00 | +0.09 | +0.00 | +0 | 0.0% | 6% | 0 | 0.0% |
| counterparty | immaterial | 2% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 26% | 0 | 0.0% |
| counterparty | immaterial | 5% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 52% | 0 | 0.0% |
| counterparty | immaterial | 10% | +0 | 0 | +0 | +0.00 | +0.00 | +0.00 | +0 | 0.0% | 78% | 0 | 0.0% |
| counterparty | uniform | 2% | -807 | 1,090 | -526 | -0.87 | +0.20 | +0.84 | -6 | 1.2% | 36% | 3,070 | 3.3% |
| counterparty | uniform | 5% | -2,359 | 3,074 | -1,750 | -3.12 | +0.76 | +2.04 | -14 | 5.2% | 69% | 4,454 | 7.5% |
| counterparty | uniform | 10% | -4,872 | 6,670 | -3,371 | -5.66 | +1.18 | +3.62 | -29 | 11.0% | 92% | 7,289 | 12.0% |
