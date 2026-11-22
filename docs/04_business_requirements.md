# 4. Business requirements (BRD extract)

Scope: the bank-side changes needed to (1) run auto-reimbursement for verified scam losses under $3,000, (2) report scam data consistently under SPF principle 4, and (3) pilot high-risk payment holds.
Priority uses MoSCoW (Must / Should / Could / Won't for this release).

## 4.1 Functional requirements
| ID | Requirement | Priority | Rationale (evidence) |
|---|---|---|---|
| BR-01 | Classify every scam complaint with one common taxonomy: scam type (NASC categories), first contact channel, payment rail, amount lost, amount recovered. | Must | Banks code the same complaint differently: ANZ's issue mix moved by up to 82 percentage points in one half-year, and Westpac records more than 98% as "Other" (Q3). |
| BR-02 | Route verified claims with a loss under $3,000 to a straight-through refund path with no full investigation. | Must | Treasury IDR position paper (May 2026). Modelled at 78% of verified claims (about 156,000 a year industry-wide, P50). |
| BR-03 | Apply verification rules before refund: customer-initiated payment, confirmed scam indicators, no prior refund for the same payment, identity confirmed. | Must | A verification pass rate of 60-95% is the third-largest driver of cost (swing analysis). |
| BR-04 | Send claims of $3,000 or more to the full investigation path, with liability assessment across the bank, telco and platform. | Must | 87% of loss dollars sit above $3,000 (about $730m a year, P50). |
| BR-05 | Record decision time, outcome and refund amount for every claim, in the same format as the ASIC IDR return. | Must | Makes SPF reports, IDR reports and the model reconcile. |
| BR-06 | Add a hold-and-call-back step for first-time payments to digital currency exchanges and new high-value payees, with a randomised hold-out group for the pilot. | Should | Top-ranked control: $65m a year in avoided losses industry-wide (P50), top 3 in 100% of simulations. |
| BR-07 | Show a Confirmation of Payee result (match / close match / no match) when a payee is added. | Should | Second-ranked control (top 3 in 94% of simulations). Targets payment-redirection scams ($166.8m in 2025). |
| BR-08 | Flag claims from customers aged 65+ for priority handling and follow-up education. | Could | People aged 65+ carry 26.5% of Scamwatch losses but are 17.2% of the population. |
| BR-09 | Automatically recover refunded amounts from other liable entities. | Won't (this release) | Depends on final SPF rules on liability apportionment. |

## 4.2 Data requirements
| ID | Field | Type | Rule |
|---|---|---|---|
| DR-01 | `scam_type` | enum (NASC list) | Mandatory on close; no "Other" without a free-text reason |
| DR-02 | `contact_channel` | enum: online, phone, SMS, email, in person, mail | Mandatory |
| DR-03 | `payment_rail` | enum: bank transfer, DCE/crypto, card, cash, other | Mandatory |
| DR-04 | `loss_amount`, `recovered_amount`, `refund_amount` | decimal AUD | `refund + recovered <= loss` |
| DR-05 | `claim_path` | enum: auto (< $3,000), investigated | Derived from `loss_amount` and verification result |
| DR-06 | `received_at`, `decided_at`, `refunded_at` | timestamp | Used for timeliness KPIs |

## 4.3 User stories with acceptance criteria
**US-01** As a scam victim with a verified loss under $3,000, I want my money back quickly without a long investigation, so that the scam does not leave me out of pocket.
- Given a claim under $3,000 that passes BR-03 verification, when it is lodged, then a refund decision is recorded automatically and the customer is told the outcome and the date.
- Given a claim that fails verification, then it moves to the investigated path with the failed rule recorded.

**US-02** As the SPF accountable executive, I want one scam dashboard built on the common taxonomy, so that I can see volumes, refunds, timeliness and AFCA escalations the same way the regulator will.
- Given BR-01 is live, when the dashboard refreshes, then every claim has a non-null scam type, channel and rail, and totals reconcile to the IDR return within 1%.

**US-03** As the payments product owner, I want to know whether holds on first-time crypto payments reduce scam losses enough to justify the friction.
- Given a randomised hold-out of flagged payments, when the pilot reaches the planned sample (about 15,000 flagged payments per arm at a 1% baseline scam rate and a 30% target reduction), then the scam-loss rate is compared between arms with a two-proportion test at alpha = 0.05.

## 4.4 Non-functional requirements
- Auditability: every refund decision keeps the rule version that produced it.
- Privacy: only the fields above are copied into the analytics layer; no free-text conversation logs.
- Model governance: the cost model is re-run each quarter with actual claims and the assumptions register is updated.
