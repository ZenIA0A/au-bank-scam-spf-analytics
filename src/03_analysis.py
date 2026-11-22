"""Step 3 - Descriptive and diagnostic analysis.

Questions answered (each writes a CSV to reports/tables and a PNG to reports/figures):
  Q1  How big is the scam problem in Australia and where do the losses come from?  (NASC)
  Q2  How are scam complaints trending at banks' internal dispute resolution (IDR)?  (ASIC)
  Q3  Can banks' scam complaint data be compared? (classification consistency)       (ASIC)
  Q4  What do banks pay scam victims through IDR today?                                (ASIC)
  Q5  Are scam complaints handled differently from other complaints? (paired test)     (ASIC)
  Q6  How many complaints escalate from each bank to AFCA?                             (ASIC + AFCA)

Run:  python src/03_analysis.py
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import style
from config import FIG, FY_HALVES, HALVES, OUT, PROCESSED, TSR
from db import connect, q

style.apply()
FIG.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
FINDINGS: dict = {}
SRC_TSR = "NASC Targeting Scams Report 2025 (combined Scamwatch, ReportCyber, AFCX, IDCARE, ASIC data)"
SRC_IDR = "ASIC IDR data file, published 16 Nov 2026 (complaints received or open, Jul 2023 - Jun 2026)"


def money(x: float) -> str:
    return f"${x/1e9:.2f}b" if x >= 1e9 else f"${x/1e6:.1f}m"


# --------------------------------------------------------------------------- Q1
def q1_scam_losses() -> None:
    yr = pd.Series(TSR["combined_loss_by_year"], name="loss").rename_axis("year").reset_index()
    by_type = (pd.Series(TSR["combined_loss_by_type_2025"], name="loss_2025").to_frame()
               .join(pd.Series(TSR["combined_loss_by_type_2024"], name="loss_2024")))
    by_type["change_pct"] = by_type.loss_2025 / by_type.loss_2024 - 1
    by_type["share_2025"] = by_type.loss_2025 / by_type.loss_2025.sum()
    pay = pd.Series(TSR["scamwatch_payment_loss_2025"], name="loss").to_frame()
    contact = (pd.Series(TSR["scamwatch_contact_loss_2025"], name="loss").to_frame()
               .join(pd.Series(TSR["scamwatch_contact_reports_with_loss_2025"], name="reports_with_loss")))
    contact["loss_per_report"] = contact.loss / contact.reports_with_loss
    yr.to_csv(OUT / "q1_losses_by_year.csv", index=False)
    by_type.to_csv(OUT / "q1_losses_by_type.csv")
    pay.to_csv(OUT / "q1_scamwatch_payment_method.csv")
    contact.to_csv(OUT / "q1_scamwatch_contact_method.csv")

    afcx = TSR["afcx_2025"]
    FINDINGS["q1"] = {
        "combined_loss_2025": TSR["combined_loss_by_year"][2025],
        "investment_share_2025": by_type.loc["Investment", "share_2025"],
        "afcx_reports_with_loss_2025": afcx["reports_with_loss"],
        "afcx_mean_loss_2025": afcx["loss"] / afcx["reports_with_loss"],
        "crypto_share_scamwatch_payment_loss": pay.loc["Cryptocurrency/DCE", "loss"] / pay.loss.sum(),
    }

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"width_ratios": [1, 1.3]})
    ax = axes[0]
    ax.bar(yr.year.astype(str), yr.loss / 1e9, color=style.BLUE, width=0.55)
    for x, v in zip(yr.year.astype(str), yr.loss / 1e9):
        ax.text(x, v + 0.05, f"${v:.1f}b", ha="center", fontsize=9, color=style.INK)
    ax.set_title("Reported scam losses, Australia")
    style.subtitle(ax, "Combined losses reported to five agencies, $ billion")
    ax.set_ylim(0, 3.6); ax.grid(axis="x", visible=False)
    ax = axes[1]
    t = by_type.sort_values("loss_2025")
    colors = [style.BLUE if i == "Investment" else style.MUTED for i in t.index]
    ax.barh(t.index, t.loss_2025 / 1e6, color=colors, height=0.55)
    for y, v in zip(t.index, t.loss_2025 / 1e6):
        ax.text(v + 10, y, f"${v:,.0f}m", va="center", fontsize=9)
    ax.set_title("2025 losses by scam type")
    style.subtitle(ax, "Investment scams alone are 38% of all reported losses, $ million")
    ax.set_xlim(0, 1050); ax.grid(axis="y", visible=False)
    style.source(fig, SRC_TSR)
    fig.tight_layout()
    style.save(fig, FIG / "f1_scam_losses.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    p = pay.sort_values("loss")
    axes[0].barh(p.index, p.loss / 1e6, color=[style.BLUE if i in ("Cryptocurrency/DCE", "Bank transfer") else style.MUTED for i in p.index], height=0.55)
    for y, v in zip(p.index, p.loss / 1e6):
        axes[0].text(v + 2, y, f"${v:.1f}m", va="center", fontsize=9)
    axes[0].set_title("How victims paid (Scamwatch, 2025)")
    style.subtitle(axes[0], "Crypto exchanges and bank transfers: 91% of losses with a known payment method, $ million")
    axes[0].set_xlim(0, 150); axes[0].grid(axis="y", visible=False)
    c = contact.sort_values("loss_per_report")
    axes[1].barh(c.index, c.loss_per_report, color=[style.BLUE if i == "Phone call" else style.MUTED for i in c.index], height=0.55)
    for y, v in zip(c.index, c.loss_per_report):
        axes[1].text(v + 600, y, f"${v:,.0f}", va="center", fontsize=9)
    axes[1].set_title("Average loss per report by first contact")
    style.subtitle(axes[1], "Phone scams: fewer victims, biggest losses (median $3,800 vs $400 overall)")
    axes[1].set_xlim(0, 45000); axes[1].grid(axis="y", visible=False)
    axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v/1000:.0f}k"))
    style.source(fig, "Scamwatch data in NASC Targeting Scams Report 2025 (Appendix 1). Average = total loss / reports with loss.")
    fig.tight_layout()
    style.save(fig, FIG / "f2_payment_contact.png")


# --------------------------------------------------------------------------- Q2
def q2_idr_trend(con) -> pd.DataFrame:
    ind = q(con, """SELECT half,
                       SUM(complaints) FILTER (WHERE issue_category = 'Scams/fraud') AS scam_fraud,
                       SUM(complaints) FILTER (WHERE issue = 'Victim of scam') AS victim_of_scam,
                       (SELECT SUM(complaint_count) FROM idr_firm f WHERE f.half = v.half) AS all_complaints
                    FROM v_industry_issue_half v GROUP BY half ORDER BY half""")
    banks = q(con, """SELECT half, SUM(scam_fraud_complaints) bank_scam_fraud, SUM(total_complaints) bank_all
                      FROM v_bank_scam_half GROUP BY half ORDER BY half""")
    ind = ind.merge(banks, on="half")
    for c in ["scam_fraud", "all_complaints", "bank_scam_fraud", "bank_all"]:
        ind[c + "_idx"] = ind[c] / ind[c].iloc[0] * 100
    ind.to_csv(OUT / "q2_idr_trend.csv", index=False)
    FINDINGS["q2"] = {
        "all_complaints_change": ind.all_complaints.iloc[-1] / ind.all_complaints.iloc[0] - 1,
        "scam_fraud_change": ind.scam_fraud.iloc[-1] / ind.scam_fraud.iloc[0] - 1,
        "scam_fraud_fy26": float(ind[ind.half.isin(FY_HALVES["FY2026"])].scam_fraud.sum()),
        "bank_share_of_scam_fraud_fy26": float(ind[ind.half.isin(FY_HALVES["FY2026"])].bank_scam_fraud.sum()
                                               / ind[ind.half.isin(FY_HALVES["FY2026"])].scam_fraud.sum()),
    }

    fig, ax = plt.subplots(figsize=(8.5, 4))
    x = np.arange(len(HALVES))
    ax.plot(x, ind.all_complaints_idx, color=style.MUTED, lw=2, marker="o", ms=5)
    ax.plot(x, ind.scam_fraud_idx, color=style.BLUE, lw=2, marker="o", ms=5)
    ax.text(x[-1] + 0.1, ind.all_complaints_idx.iloc[-1], f"All IDR complaints  {ind.all_complaints_idx.iloc[-1]:.0f}", va="center", fontsize=9, color=style.INK_2)
    ax.text(x[-1] + 0.1, ind.scam_fraud_idx.iloc[-1], f"Scam & fraud complaints  {ind.scam_fraud_idx.iloc[-1]:.0f}", va="center", fontsize=9, color=style.INK)
    ax.axhline(100, color=style.INK_2, lw=0.8)
    ax.set_xticks(x, HALVES); ax.set_xlim(-0.3, len(HALVES) + 1.6)
    ax.set_title("Scam complaints at IDR have not grown with other complaints")
    style.subtitle(ax, "Index, 2023 HY2 = 100, all financial firms reporting to ASIC")
    style.source(fig, SRC_IDR)
    style.save(fig, FIG / "f3_idr_trend.png")
    return ind


# --------------------------------------------------------------------------- Q3
def q3_taxonomy(con) -> pd.DataFrame:
    mix = q(con, """SELECT b.short AS bank, i.half, i.issue, SUM(i.complaint_count) AS n
                    FROM idr_issue i JOIN bank_map b USING (firm_name)
                    WHERE i.issue_category = 'Scams/fraud' AND b.tier = 'Major bank'
                    GROUP BY ALL""")
    piv = mix.pivot_table(index=["bank", "half"], columns="issue", values="n", aggfunc="sum").fillna(0)
    share = piv.div(piv.sum(axis=1), axis=0)
    share.to_csv(OUT / "q3_major_bank_scam_issue_mix.csv")
    # A simple, explainable instability score: largest half-on-half swing in any issue's share
    swing = share.groupby(level=0).diff().abs().max(axis=1).groupby(level=0).max()
    FINDINGS["q3"] = {"max_half_on_half_share_swing": swing.round(2).to_dict(),
                      "westpac_victim_of_scam_share_2026H1": float(share.loc[("Westpac", "2026 HY1")].get("Victim of scam", 0))}

    issues = ["Victim of scam", "Other scam/fraud-related issues", "Fraud/forgery by a third party", "Fraud/forgery by financial firm"]
    colors = dict(zip(issues, style.SERIES[:4]))
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.8), sharey=True)
    for ax, bank in zip(axes, ["CBA", "NAB", "ANZ", "Westpac"]):
        s = share.loc[bank].reindex(HALVES).fillna(0)
        bottom = np.zeros(len(s))
        for iss in issues:
            v = s.get(iss, pd.Series(0, index=s.index)).values
            ax.bar(range(len(s)), v, bottom=bottom, color=colors[iss], width=0.72, edgecolor=style.SURFACE, linewidth=1)
            bottom += v
        ax.set_title(bank); ax.set_xticks(range(len(s)), [h.replace(" HY", "\nH") for h in HALVES], fontsize=8)
        ax.grid(axis="x", visible=False); ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    fig.legend([plt.Rectangle((0, 0), 1, 1, color=colors[i]) for i in issues], issues, ncol=4,
               loc="lower center", bbox_to_anchor=(0.5, 0.0), fontsize=9)
    fig.suptitle("The same scam complaint is labelled differently by each major bank - and changes over time",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.text(0.01, 0.905, "Share of each bank's Scams/fraud IDR complaints by issue code", fontsize=9, color=style.INK_2)
    style.source(fig, SRC_IDR + ". ANZ moved most scam complaints to 'Other' from 2025 HY1; Westpac uses 'Other' almost exclusively.")
    fig.tight_layout(rect=(0, 0.07, 1, 0.9))
    style.save(fig, FIG / "f4_taxonomy.png")
    return share


# --------------------------------------------------------------------------- Q4
def q4_remedies(con) -> pd.DataFrame:
    paid = q(con, """SELECT o.half, o.issue,
                        SUM(o.complaint_count) AS monetary_remedies,
                        SUM(o.complaint_count * o.average_monetary_remedy) AS amount_paid,
                        SUM(o.complaint_count) FILTER (WHERE o.average_monetary_remedy IS NULL) AS remedies_without_amount
                     FROM idr_issue_outcome o
                     WHERE o.outcome = 'Monetary remedy'
                       AND o.issue IN ('Victim of scam', 'Other scam/fraud-related issues',
                                       'Fraud/forgery by a third party', 'Fraud/forgery by financial firm')
                     GROUP BY ALL ORDER BY 1, 2""")
    paid.to_csv(OUT / "q4_scam_remedies_by_issue.csv", index=False)
    tot = paid.groupby("half")[["monetary_remedies", "amount_paid"]].sum()
    tot["avg_remedy"] = tot.amount_paid / tot.monetary_remedies
    tot.to_csv(OUT / "q4_scam_remedies_total.csv")
    fy26 = tot.loc[FY_HALVES["FY2026"]].sum()
    bank_fy26 = q(con, """SELECT b.short bank, b.tier,
                            SUM(o.complaint_count) remedies,
                            SUM(o.complaint_count * o.average_monetary_remedy) paid
                          FROM idr_issue_outcome o JOIN bank_map b USING (firm_name)
                          WHERE o.outcome='Monetary remedy' AND o.half IN ('2025 HY2','2026 HY1')
                            AND o.issue IN ('Victim of scam','Other scam/fraud-related issues',
                                            'Fraud/forgery by a third party','Fraud/forgery by financial firm')
                          GROUP BY ALL ORDER BY paid DESC""")
    sc = q(con, """SELECT bank, SUM(scam_fraud_complaints) scam_fraud FROM v_bank_scam_half
                   WHERE half IN ('2025 HY2','2026 HY1') GROUP BY 1""")
    bank_fy26 = bank_fy26.merge(sc, on="bank")
    bank_fy26["remedy_rate"] = bank_fy26.remedies / bank_fy26.scam_fraud
    bank_fy26["avg_remedy"] = bank_fy26.paid / bank_fy26.remedies
    bank_fy26.to_csv(OUT / "q4_bank_remedies_fy26.csv", index=False)
    afcx_loss = TSR["afcx_2025"]["loss"]
    FINDINGS["q4"] = {
        "idr_scam_remedies_paid_fy26": float(fy26.amount_paid),
        "idr_scam_remedies_count_fy26": float(fy26.monetary_remedies),
        "idr_scam_avg_remedy_fy26": float(fy26.amount_paid / fy26.monetary_remedies),
        "paid_vs_afcx_loss_ratio": float(fy26.amount_paid / afcx_loss),
        "paid_change_2023H2_to_2026H1": float(tot.amount_paid.iloc[-1] / tot.amount_paid.iloc[0] - 1),
    }

    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ax.bar(range(len(tot)), tot.amount_paid / 1e6, color=style.BLUE, width=0.55)
    for i, v in enumerate(tot.amount_paid / 1e6):
        ax.text(i, v + 0.6, f"${v:.1f}m", ha="center", fontsize=9)
    ax.set_xticks(range(len(tot)), tot.index); ax.grid(axis="x", visible=False)
    ax.set_title("Money returned to scam & fraud complainants at IDR is falling")
    style.subtitle(ax, "Monetary remedies on Scams/fraud complaints, all firms, $ million per half-year (count x average remedy)")
    style.source(fig, SRC_IDR + ". Excludes refunds made outside the complaints process.")
    style.save(fig, FIG / "f5_remedies.png")
    return bank_fy26


# --------------------------------------------------------------------------- Q5
def q5_paired_test(con) -> pd.DataFrame:
    """Within the same firm and half-year, are scam/fraud complaints closed within 30 days
    more or less often than the firm's complaints overall? Wilcoxon signed-rank on the
    paired differences; only cells with >= 50 closed scam/fraud complaints are used."""
    d = q(con, """WITH s AS (
                    SELECT firm_name, half,
                           SUM(count_of_closed_complaints) closed,
                           SUM(pct_resolved_within_30_days * count_of_closed_complaints)
                               / NULLIF(SUM(count_of_closed_complaints), 0) p30_scam
                    FROM idr_issue WHERE issue_category = 'Scams/fraud' GROUP BY ALL)
                  SELECT s.*, f.pct_resolved_within_30_days p30_all
                  FROM s JOIN idr_firm f USING (firm_name, half)
                  WHERE s.closed >= 50""")
    d["diff_pp"] = (d.p30_scam - d.p30_all) * 100
    w = stats.wilcoxon(d.p30_scam, d.p30_all)
    d.to_csv(OUT / "q5_scam_vs_all_30day.csv", index=False)
    FINDINGS["q5"] = {"n_firm_halves": int(len(d)), "n_firms": int(d.firm_name.nunique()),
                      "median_diff_pp": float(d.diff_pp.median()), "mean_diff_pp": float(d.diff_pp.mean()),
                      "share_gap_worse_than_5pp": float((d.diff_pp < -5).mean()),
                      "share_scam_faster": float((d.diff_pp > 0).mean()),
                      "wilcoxon_p": float(w.pvalue)}

    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    ax.hist(d.diff_pp.clip(-30, 30), bins=30, color=style.BLUE, edgecolor=style.SURFACE)
    ax.axvline(0, color=style.INK, lw=1)
    ax.set_xlabel("Scam/fraud % closed within 30 days minus firm's overall %, percentage points")
    ax.set_title("Scam & fraud complaints close within 30 days slightly less often")
    style.subtitle(ax, f"{len(d)} firm half-years ({d.firm_name.nunique()} firms) with >= 50 closed scam/fraud complaints; "
                       f"median gap {d.diff_pp.median():+.1f} pp, Wilcoxon p = {w.pvalue:.1g}")
    ax.grid(axis="x", visible=False)
    style.source(fig, SRC_IDR + ". Values clipped at +/-30 pp for display.")
    style.save(fig, FIG / "f6_paired_test.png")
    return d


# --------------------------------------------------------------------------- Q6
def q6_escalation(con) -> pd.DataFrame:
    e = q(con, "SELECT * FROM v_escalation_fy26 ORDER BY escalation_rate DESC")
    e["afca_closed_at_referral_share"] = e.afca_closed_at_referral / e.afca_received_fy26
    med = q(con, """SELECT b.short bank,
                      SUM(f.median_time_taken * f.count_of_closed_complaints) / SUM(f.count_of_closed_complaints) median_days_wtd,
                      SUM(f.pct_resolved_within_30_days * f.count_of_closed_complaints) / SUM(f.count_of_closed_complaints) p30
                    FROM idr_firm f JOIN bank_map b USING (firm_name)
                    WHERE half IN ('2025 HY2','2026 HY1') GROUP BY 1""")
    e = e.merge(med, on="bank")
    e.to_csv(OUT / "q6_escalation_fy26.csv", index=False)
    core = e[e.bank != "Revolut"]
    rho = stats.spearmanr(core.p30, core.escalation_rate)
    majors = e[e.tier == "Major bank"]
    FINDINGS["q6"] = {
        "escalation": e.set_index("bank").escalation_rate.round(4).to_dict(),
        "major_bank_escalation": float(majors.afca_received_fy26.sum() / majors.idr_complaints_fy26.sum()),
        "spearman_p30_vs_escalation_rho": float(rho.statistic), "spearman_p": float(rho.pvalue),
        "n_banks_in_test": int(len(core)),
    }

    s = e.sort_values("escalation_rate")
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    colors = [style.ORANGE if b == "Revolut" else (style.BLUE if t == "Major bank" else style.MUTED)
              for b, t in zip(s.bank, s.tier)]
    vals = (s.escalation_rate * 100).clip(upper=4.2)
    ax.barh(s.bank, vals, color=colors, height=0.6)
    for y, v, raw in zip(s.bank, vals, s.escalation_rate * 100):
        ax.text(v + 0.05, y, f"{raw:.1f}%" + ("  (axis cut)" if raw > 4.2 else ""), va="center", fontsize=9)
    ax.set_xlim(0, 5); ax.grid(axis="y", visible=False)
    ax.set_title("How many complaints end up at AFCA? (FY2026)")
    style.subtitle(ax, "AFCA complaints received / IDR complaints received or open, same 12 months. Blue = major banks")
    style.source(fig, "AFCA Datacube (Compare firms, Bank, FY2025-26) and ASIC IDR (2025 HY2 + 2026 HY1). Licence-level: "
                      "Westpac includes St George, Bank of Melbourne, BankSA; CBA includes Bankwest.")
    style.save(fig, FIG / "f7_escalation.png")
    return e


def main() -> None:
    con = connect()
    q1_scam_losses()
    q2_idr_trend(con)
    q3_taxonomy(con)
    q4_remedies(con)
    q5_paired_test(con)
    q6_escalation(con)
    (PROCESSED / "findings.json").write_text(json.dumps(FINDINGS, indent=2, default=float))
    print(json.dumps(FINDINGS, indent=2, default=float))


if __name__ == "__main__":
    main()
