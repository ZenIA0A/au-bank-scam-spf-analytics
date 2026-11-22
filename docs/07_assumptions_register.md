# 7. Assumptions register

Every model input is either **DATA** (from a published source) or an **ASSUMPTION** (a planning range a bank would replace with its own numbers). Ranges are sampled 100,000 times in `src/04_spf_model.py`. "Swing" is how far the FY2028 net cost moves when the input goes from its P10 to its P90 with everything else held at the median.

| Input | Type | Value / range | Basis | Swing on net cost |
|---|---|---|---|---|
| Bank-reported scam reports with loss (2025) | DATA | 199,666 | NASC TSR 2025, Table 2 (AFCX) | - |
| Mean loss per bank-reported scam | DATA-anchored | $4,219 +/-15% | $842.3m / 199,666 | $5.0m |
| Median loss per scam | DATA-anchored | $400 - $1,000 | Scamwatch median $400 (2025); major banks' median IDR scam remedy $380-$1,000 | $28.5m |
| Annual growth to FY2028 | ASSUMPTION | -10% to +15% (mode +2%) | AFCX +21.9% in 2025 but flagged as not comparable; Scamwatch reports -19.6% | **$29.1m** |
| Extra claims from automatic refunds | ASSUMPTION | x1.0 - x1.5 (mode 1.15) | Victims who never complained will claim once refunds are certain | $20.2m |
| Share of claims verified | ASSUMPTION | 60% - 95% (mode 80%) | Some claims are not scams (disputes, first-party fraud) | $21.2m |
| Investigation hours avoided per auto-refund | ASSUMPTION | 1 - 4 hours (mode 2.5) | Typical scam investigation effort; replace with time-and-motion data | $17.4m |
| Verification hours per auto-refund | ASSUMPTION | 0.25 - 0.75 hours | Light-touch checks under BR-03 | $4.2m |
| Fully loaded case-officer cost | ASSUMPTION | $55 - $80 per hour | Planning range | $6.2m |
| Scam complaints escalating to AFCA | DATA-anchored | 3.7% x (0.3 - 0.8) | 6,580 AFCA banking scam complaints FY26 / 178,091 IDR scam & fraud complaints; small claims escalate less | $1.6m |
| AFCA share closed at referral | DATA | 65.1% | AFCA Datacube, peer banks FY26 | - |
| AFCA fee per escalation | DATA | $99.56 at referral; $1,181-$2,316 at case management | AFCA Complaint Fee Guide (FY25) x 1.035 | - |
| Today's IDR scam remedies | DATA | $39.7m, average $1,973 | ASIC IDR FY26 | - |
| Median of today's remedies | DATA-anchored | $400 - $650 | ASIC IDR, major banks | $2.1m |
| Control effectiveness | ASSUMPTION | see `05_prioritisation.py` (e.g. holds 10-30%, CoP 25-50%) | Planning ranges, to be replaced by pilot results | ranking reported as P(top 3) |
| Control effort / friction | ASSUMPTION (judgement) | 1-5 scores | Delivery complexity and customer friction | - |

**What to do with this register:** the four largest swings (growth, median loss, verification rate, extra claims) are where a bank's own data would most improve the estimate. They should be the first things measured once claims start flowing.
