# 5. Process map: scam claim handling, current vs future state

## Current state (simplified)
Every scam complaint goes through the same investigation, whatever the amount. Most end without any money returned: today about 1 in 9 scam and fraud complaints gets a monetary remedy (20,141 remedies on 178,091 scam/fraud complaints across all firms in FY26).

```mermaid
flowchart LR
  A[Customer reports scam] --> B[Fraud team: stop / recall attempt]
  B --> C[Complaint logged at IDR<br/>issue code varies by bank]
  C --> D[Full investigation<br/>every claim]
  D --> E{Outcome}
  E -->|~1 in 9| F[Monetary remedy<br/>avg $1,973]
  E -->|most| G[Explanation / service remedy]
  G --> H[Customer may escalate to AFCA<br/>~1-2% of all bank complaints]
```

## Future state under the SPF (recommended)
```mermaid
flowchart LR
  A[Customer reports scam] --> B[Fraud team: stop / recall attempt]
  B --> C[Claim logged with common taxonomy<br/>type, channel, rail, amount]
  C --> D{Verified?}
  D -->|No| X[Investigated path<br/>reason recorded]
  D -->|Yes| E{Loss < $3,000?}
  E -->|Yes ~78% of claims| F[Straight-through refund<br/>no full investigation]
  E -->|No ~22% of claims<br/>87% of loss dollars| G[Investigation + liability<br/>apportionment bank / telco / platform]
  F --> H[SPF & IDR reporting<br/>same data model]
  G --> H
  X --> H
```

## What changes, and why it matters
| Step | Change | Benefit (modelled, industry, FY2028 P50) |
|---|---|---|
| Classification | One taxonomy at intake (BR-01) | Comparable reporting; the model can be recalibrated with real data |
| Small claims | Straight-through refund | $20.5m of investigation effort avoided; $2.1m of AFCA fees avoided |
| Large claims | Investigation kept, focus on liability | Effort concentrated where 87% of the money is |
| Prevention | Holds and Confirmation of Payee | $65m + $24m of avoided losses (P50, before overlap) |
