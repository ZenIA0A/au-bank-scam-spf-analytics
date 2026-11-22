# Executive memo: Getting ready for the Scams Prevention Framework

**To:** SPF Accountable Executive, Chief Risk Officer
**From:** James Lai, Business Analytics
**Date:** 22 November 2026
**Decision needed:** approve four workstreams and a FY2028 provision range before the SPF obligations start on 31 March 2027.

---

## Bottom line
1. **Auto-refunding verified scam losses under $3,000 is affordable but not free.** For the banking industry it adds about **$74m net in FY2028** (80% range $51m-$102m), **almost twice what banks returned to scam complainants through IDR in FY26 ($39.7m)**.
2. **It solves the volume problem, not the money problem.** About **78% of claims** fall under $3,000 but they hold only **about 13% of loss dollars**. Roughly **$730m a year** of bank-reported losses stays in larger scams, so prevention, not refunds, has to carry the dollar reduction.
3. **Our scam data is not ready.** The major banks label the same scam complaint in incompatible ways, and ANZ's labels moved by 82 percentage points in one half-year. Without one taxonomy we cannot run the $3,000 rule, report under SPF principle 4, or measure whether controls work.

## What the data shows
| Finding | Evidence |
|---|---|
| Scam losses remain high | $2.18b reported in 2025 (+7.8%). Banks recorded 199,666 loss reports worth $842.3m (mean $4,219). Investment scams are 38% of losses. |
| Losses travel on rails banks control | In Scamwatch data, crypto exchanges ($121.3m) and bank transfers ($118.1m) carry 91% of losses with a known payment method. |
| Few complainants get money back today | 178,091 scam and fraud complaints at IDR in FY26, but only 20,141 monetary remedies (average $1,973). Money returned fell 46% from 2023 H2 to 2026 H1. |
| Scam complaints are not faster to close | Across 231 firm half-years, scam and fraud complaints close within 30 days slightly less often than each firm's other complaints (median -0.3 pp, Wilcoxon p < 0.001). |
| AFCA escalation depends on how firms record complaints, not on speed | 1.9% of major-bank IDR complaints reached AFCA in FY26 (ANZ 1.2%, CBA 2.4%). Across 12 banks there is no link between the 30-day closure rate and escalation (Spearman rho = -0.13, p = 0.70). |

## What drives the cost estimate
The four inputs that move the FY2028 cost most are the **growth in scam losses** ($29m swing), the **median scam loss** ($29m), the **share of claims that pass verification** ($21m) and **extra claims triggered by automatic refunds** ($20m). All four become measurable within one quarter of go-live. The model is built to be re-run with real claims.

## Recommendations
| # | Action | Owner | By | KPI |
|---|---|---|---|---|
| 1 | **Adopt one scam taxonomy and data model** (scam type, channel, payment rail, loss, recovery, refund) across fraud ops, IDR and SPF reporting. | Data & Analytics | Feb 2027 | 100% of scam claims fully coded; IDR and SPF totals reconcile within 1% |
| 2 | **Build a straight-through "verify and refund" path for claims under $3,000** with explicit verification rules; keep full investigation for larger claims. | Fraud & Scams Ops + Complaints | Mar 2027 | Refund decision time; verification pass rate; AFCA escalation rate on small claims |
| 3 | **Provision at P50 and stress-test at P90** of the cost model (industry $74m / $102m; bank-level figures in the dashboard), and re-run the model each quarter. | Finance | Jan 2027 | Forecast error vs actual claims |
| 4 | **Pilot holds and limits on first-time high-risk payments** (crypto exchanges, new high-value payees) with a randomised hold-out, then roll out **Confirmation of Payee**. They rank first and second for avoided loss per unit of effort (top 3 in 100% and 94% of simulations). | Payments product + Data & Analytics | Pilot Feb-Apr 2027 | Scam-loss rate per flagged payment; customer drop-off |

**Pilot sizing:** at a 1% scam rate among flagged payments, detecting a 30% reduction needs about **14,600 flagged payments per arm** (alpha 0.05, power 0.8), or about 34,900 per arm for a 20% reduction.

## Roadmap
```
Dec 2026  Jan 2027  Feb 2027  Mar 2027  Apr 2027  May 2027  Jun 2027
[1 Taxonomy & data model ]
          [3 Provision]
          [2 Verify-and-refund build & test ][Go-live 31 Mar -> monitor, recalibrate ]
                    [4 Holds pilot (randomised)   ][Scale or stop -> CoP rollout   ]
```

## Limits of this analysis
Public data only, at firm level. Industry figures are modelled; bank-level figures depend on how complaints are allocated (two methods are shown). Control effectiveness is assumed and must be replaced by pilot results. Full assumptions: `docs/07_assumptions_register.md`.
