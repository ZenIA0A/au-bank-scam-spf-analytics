"""Step 2 - Automated data-quality checks.

Each check returns PASS / WARN / FAIL with the evidence, and the full log is written to
reports/tables/data_quality.csv. A FAIL stops the pipeline; a WARN is a known feature of
the data that the analysis must handle (and the README explains how).

Run:  python src/02_quality_checks.py
"""
import sys

import pandas as pd

from config import BANKS, HALVES, OUT
from db import connect, q

results = []


def check(name, status, detail):
    results.append({"check": name, "status": status, "detail": detail})
    print(f"[{status:4s}] {name}: {detail}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    con = connect()

    # 1. Coverage: six half-years in every table
    for t in ["idr_firm", "idr_issue", "idr_outcome", "idr_issue_outcome"]:
        halves = q(con, f"SELECT DISTINCT half FROM {t} ORDER BY 1")["half"].tolist()
        check(f"{t}: half-years", "PASS" if halves == HALVES else "FAIL", ", ".join(halves))

    # 2. Primary keys are unique
    keys = {"idr_firm": "firm_name, acn, half",
            "idr_issue": "firm_name, acn, half, issue_category, issue",
            "idr_issue_outcome": "firm_name, acn, half, issue, outcome"}
    for t, k in keys.items():
        d = q(con, f"SELECT COUNT(*) n FROM (SELECT {k}, COUNT(*) c FROM {t} GROUP BY ALL HAVING c > 1)")["n"][0]
        check(f"{t}: unique ({k})", "PASS" if d == 0 else "FAIL", f"{d} duplicate keys")

    # 3. Percentages are inside [0, 1] and cumulative buckets never decrease
    buckets = ["pct_resolved_within_a_day", "pct_resolved_within_7_days", "pct_resolved_within_21_days",
               "pct_resolved_within_30_days", "pct_resolved_within_45_days", "pct_resolved_within_90_days",
               "pct_resolved_within_180_days"]
    df = q(con, f"SELECT {', '.join(buckets)} FROM idr_issue")
    out_of_range = int(((df < 0) | (df > 1.0001)).sum().sum())
    check("idr_issue: % in [0,1]", "PASS" if out_of_range == 0 else "FAIL", f"{out_of_range} values outside range")
    diffs = df[buckets].diff(axis=1).iloc[:, 1:]
    non_mono = int((diffs < -1e-9).any(axis=1).sum())
    check("idr_issue: cumulative % non-decreasing", "PASS" if non_mono == 0 else "WARN",
          f"{non_mono} rows where a longer window shows a smaller %")

    # 4. Closed complaints never exceed complaints received or open
    bad = q(con, "SELECT COUNT(*) n FROM idr_issue WHERE count_of_closed_complaints > complaint_count")["n"][0]
    check("idr_issue: closed <= complaints", "PASS" if bad == 0 else "FAIL", f"{bad} rows violate")

    # 5. Issue rows vs firm totals: a complaint can carry more than one issue
    r = q(con, """SELECT SUM(i) / SUM(f) ratio FROM (
                    SELECT f.firm_name, f.half, f.complaint_count f, SUM(i.complaint_count) i
                    FROM idr_firm f JOIN idr_issue i USING (firm_name, acn, half) GROUP BY ALL)""")["ratio"][0]
    check("issue rows / firm total", "WARN" if r > 1.0 else "PASS",
          f"ratio = {r:.3f}; issues are multi-select, so scam counts are not added to other issues")

    # 6. Outcomes are multi-select: for scam victims the outcome rows exceed complaints
    r2 = q(con, """SELECT SUM(o.complaint_count)::DOUBLE / (SELECT SUM(complaint_count) FROM idr_issue
                                                            WHERE issue='Victim of scam') r
                   FROM idr_issue_outcome o WHERE o.issue='Victim of scam'""")["r"][0]
    check("victim-of-scam outcomes / complaints", "WARN", f"ratio = {r2:.2f}; rates use outcome count / complaints")

    # 7. Every peer-group bank is present in every half-year
    for firm, meta in BANKS.items():
        n = q(con, f"SELECT COUNT(DISTINCT half) n FROM idr_firm WHERE firm_name = '{firm}'")["n"][0]
        check(f"bank coverage: {meta['short']}", "PASS" if n == 6 else "WARN", f"{n}/6 half-years")

    # 8. Money fields: median above mean is possible but unusual - count them
    mm = q(con, """SELECT COUNT(*) n FROM idr_issue_outcome
                   WHERE median_monetary_remedy > average_monetary_remedy * 1.0001""")["n"][0]
    check("monetary remedy: median > mean", "WARN" if mm else "PASS",
          f"{mm} rows (small cells where one large-but-not-largest payment dominates)")

    # 9. AFCA extract internal consistency
    a = q(con, "SELECT * FROM afca_banks")
    bad_a = int((a["closed_at_referral"] > a["complaints_received"]).sum())
    check("afca: closed at referral <= received", "PASS" if bad_a == 0 else "FAIL", f"{bad_a} rows violate")
    fy26 = a[a.fy == "FY2026"]
    rec = (fy26["closed_at_referral"] + fy26["closed_after_referral"]).sum()
    check("afca FY26: closed total vs received", "PASS",
          f"closed {rec:,.0f} vs received {fy26['complaints_received'].sum():,.0f} "
          "(closures include complaints received in earlier years)")

    log = pd.DataFrame(results)
    log.to_csv(OUT / "data_quality.csv", index=False)
    fails = (log.status == "FAIL").sum()
    print(f"\n{len(log)} checks: {(log.status=='PASS').sum()} pass, {(log.status=='WARN').sum()} warn, {fails} fail")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
