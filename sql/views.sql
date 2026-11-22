-- Analytical layer over the typed ASIC IDR tables (DuckDB SQL).
-- Built by src/03_analysis.py after bank_map has been loaded from src/config.py.
-- Conventions
--   * "complaints" = complaints received or open in the half-year (ASIC definition)
--   * time-to-resolve %s are shares of CLOSED complaints, so they are re-weighted by
--     count_of_closed_complaints when rows are combined
--   * outcomes are multi-select at IDR, so outcome rates are outcome count / complaints

-- 1. Industry view: complaints by issue category and half-year (all firms)
CREATE OR REPLACE VIEW v_industry_issue_half AS
SELECT half, issue_category, issue,
       SUM(complaint_count) AS complaints,
       SUM(count_of_closed_complaints) AS closed,
       SUM(pct_resolved_within_30_days * count_of_closed_complaints)
           / NULLIF(SUM(count_of_closed_complaints), 0) AS pct_within_30d
FROM idr_issue
GROUP BY ALL;

-- 2. Firm totals per half (denominator for scam share)
CREATE OR REPLACE VIEW v_firm_half AS
SELECT f.firm_name, f.half, f.complaint_count AS total_complaints,
       f.count_of_closed_complaints AS total_closed,
       f.pct_resolved_within_30_days AS total_pct_within_30d,
       f.median_time_taken AS total_median_days
FROM idr_firm f;

-- 3. Scam/fraud issues per bank per half-year
CREATE OR REPLACE VIEW v_bank_scam_half AS
WITH s AS (
    SELECT i.firm_name, i.half,
           SUM(i.complaint_count) FILTER (WHERE i.issue_category = 'Scams/fraud') AS scam_fraud_complaints,
           SUM(i.complaint_count) FILTER (WHERE i.issue = 'Victim of scam') AS victim_of_scam,
           SUM(i.count_of_closed_complaints) FILTER (WHERE i.issue = 'Victim of scam') AS victim_closed,
           MAX(i.pct_resolved_within_30_days) FILTER (WHERE i.issue = 'Victim of scam') AS victim_pct_within_30d,
           MAX(i.median_time_taken) FILTER (WHERE i.issue = 'Victim of scam') AS victim_median_days
    FROM idr_issue i
    GROUP BY ALL
)
SELECT b.short AS bank, b.tier, s.*, f.total_complaints, f.total_pct_within_30d,
       s.scam_fraud_complaints::DOUBLE / f.total_complaints AS scam_share_of_complaints
FROM s
JOIN bank_map b ON b.firm_name = s.firm_name
JOIN v_firm_half f ON f.firm_name = s.firm_name AND f.half = s.half;

-- 4. What happens to scam victims' complaints at IDR: outcome mix and money paid
CREATE OR REPLACE VIEW v_bank_victim_outcome AS
SELECT b.short AS bank, b.tier, o.half, o.outcome,
       o.complaint_count AS outcome_count,
       o.average_monetary_remedy, o.median_monetary_remedy
FROM idr_issue_outcome o
JOIN bank_map b ON b.firm_name = o.firm_name
WHERE o.issue = 'Victim of scam';

CREATE OR REPLACE VIEW v_bank_victim_money AS
SELECT v.bank, v.tier, v.half,
       s.victim_of_scam,
       v.outcome_count AS monetary_remedy_count,
       v.outcome_count::DOUBLE / s.victim_of_scam AS monetary_remedy_rate,
       v.average_monetary_remedy, v.median_monetary_remedy,
       v.outcome_count * v.average_monetary_remedy AS est_amount_paid
FROM v_bank_victim_outcome v
JOIN v_bank_scam_half s ON s.bank = v.bank AND s.half = v.half
WHERE v.outcome = 'Monetary remedy';

-- 5. Escalation: AFCA complaints received in FY2026 vs IDR complaints in the same
--    twelve months (2025 HY2 + 2026 HY1), at licence (group) level
CREATE OR REPLACE VIEW v_escalation_fy26 AS
WITH idr AS (
    SELECT b.short AS bank, b.tier, SUM(f.complaint_count) AS idr_complaints_fy26
    FROM idr_firm f JOIN bank_map b ON b.firm_name = f.firm_name
    WHERE f.half IN ('2025 HY2', '2026 HY1')
    GROUP BY ALL
), afca AS (
    SELECT m.short AS bank,
           SUM(a.complaints_received) AS afca_received_fy26,
           SUM(a.closed_at_referral) AS afca_closed_at_referral,
           SUM(a.complaints_accepted) AS afca_accepted,
           SUM(a.in_favour_complainant) AS afca_in_favour_complainant,
           SUM(a.resolved_by_agreement) AS afca_resolved_by_agreement
    FROM afca_banks a JOIN bank_afca_map m ON m.afca_name = a.firm
    WHERE a.fy = 'FY2026'
    GROUP BY ALL
)
SELECT idr.*, afca.* EXCLUDE (bank),
       afca.afca_received_fy26::DOUBLE / idr.idr_complaints_fy26 AS escalation_rate,
       afca.afca_received_fy26 * 10000.0 / idr.idr_complaints_fy26 AS afca_per_10k_idr
FROM idr JOIN afca USING (bank);
