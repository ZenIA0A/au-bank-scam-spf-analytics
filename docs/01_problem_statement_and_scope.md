# 1. Problem statement and scope

## Context
Australia's **Scams Prevention Framework (SPF)** makes banks, telcos and digital platforms legally responsible for preventing, detecting, disrupting, reporting and responding to scams. Most obligations start on **31 March 2027**, and regulated entities had to join AFCA by **1 September 2026**. Penalties reach **$50 million**.

In May 2026 Treasury's *Internal Dispute Resolution under the SPF* position paper proposed that regulated entities **automatically reimburse verified scam losses under $3,000** without a full investigation, and share liability equally between entities that breached their obligations.

At the same time, Australians reported **$2.18 billion** in scam losses in 2025 (+7.8%). Banks themselves recorded **199,666 scam reports with a loss totalling $842.3 million** (AFCX data in the NASC Targeting Scams Report 2025).

## Problem statement
> A major Australian bank must be ready for the SPF by 31 March 2027, but it does not yet know (a) how much the proposed $3,000 auto-reimbursement will cost, (b) whether its scam complaint data is fit to run and report on the new process, or (c) which prevention controls will cut the losses that auto-reimbursement does not cover.

## Business questions
| # | Question | Answered in |
|---|---|---|
| BQ1 | How large is the scam problem, and where do the losses come from? | `03_analysis.py` Q1, figure f1-f2 |
| BQ2 | How do banks handle scam complaints today (volume, speed, money returned)? | Q2, Q4, Q5 |
| BQ3 | Can scam complaint data be compared and reported consistently? | Q3 |
| BQ4 | How often do complaints escalate to AFCA, and what drives it? | Q6 |
| BQ5 | What will auto-reimbursement under $3,000 cost in its first full year (FY2028)? | `04_spf_model.py` |
| BQ6 | Which controls should be funded first to reduce the losses it does not cover? | `05_prioritisation.py` |

## In scope
- Banks reporting to ASIC IDR and AFCA (13-bank peer group: 4 majors, 8 other banks, 1 digital bank).
- Scam and fraud complaints at IDR, Jul 2023 to Jun 2026 (six half-years).
- Industry-wide scam losses 2021-2025 (NASC combined data).

## Out of scope
- Telco and digital-platform obligations under the SPF (only the bank side is modelled).
- Card fraud handled under the ePayments Code and chargeback schemes.
- Customer-level or transaction-level data. All data is public and aggregated, so the model is built to be **recalibrated with a bank's internal data**.

## Success criteria for the analysis
1. Every figure traces back to a public source file or a labelled assumption (see `07_assumptions_register.md`).
2. The cost estimate is a range (P10 / P50 / P90), with the assumptions ranked by how much they move the answer.
3. The recommendation names owners, dates and KPIs, so it can be acted on.
