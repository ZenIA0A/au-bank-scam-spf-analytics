"""Step 4 - What will the proposed SPF auto-reimbursement cost, and what does it save?

Treasury's IDR position paper (May 2026) proposes that regulated entities automatically
reimburse verified scam losses under $3,000 without a full investigation. This script
estimates the first full year of that rule (FY2028) for the banking industry and for each
peer bank, using a Monte Carlo simulation.

Every input is tagged DATA (from a published source) or ASSUMPTION (a planning range that a
bank would replace with its own numbers). The ranges, not single guesses, carry through to
P10 / P50 / P90 outputs, and a swing analysis shows which assumption matters most.

Run:  python src/04_spf_model.py
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import style
from config import AFCA_FEES, AFCA_FY26_UPLIFT, FIG, OUT, PROCESSED, TSR
from db import connect, q

style.apply()
RNG = np.random.default_rng(20261122)
N_DRAWS = 100_000
THRESHOLD = 3_000.0
YEARS_AHEAD = 2.5  # calendar 2025 (mid-point) -> FY2028 (mid-point Dec 2027)


def tri(lo, mode, hi, n):
    return RNG.triangular(lo, mode, hi, n)


def build_inputs(n: int, base: dict) -> dict:
    """Sample every uncertain input. Comments say where each range comes from."""
    return {
        # DATA: AFCX (bank-reported scam reports with a loss), NASC Targeting Scams Report 2025, Table 2
        "n0": np.full(n, base["afcx_reports_with_loss"]),
        # ASSUMPTION: annual growth in bank-reported scam losses to FY2028. AFCX rose 21.9% in 2025
        # but NASC warns the series is not comparable year to year; Scamwatch reports fell 19.6%.
        "growth": tri(-0.10, 0.02, 0.15, n),
        # ASSUMPTION: extra claims because refunds become automatic (victims who never complained)
        "uptake": tri(1.00, 1.15, 1.50, n),
        # DATA-anchored: mean loss per AFCX report = $842.3m / 199,666 = $4,219 (+/-15% for drift)
        "mean_loss": base["afcx_mean_loss"] * RNG.uniform(0.85, 1.15, n),
        # DATA-anchored: median loss. Scamwatch median $400 (2025) is the floor; the major banks'
        # median IDR scam remedy ranged ~$380-$1,000 across 2023-26, so the ceiling is $1,000.
        "median_loss": RNG.uniform(400, 1000, n),
        # ASSUMPTION: share of claims that pass verification as genuine scam losses
        "verified": tri(0.60, 0.80, 0.95, n),
        # ASSUMPTION: investigation hours no longer needed per auto-reimbursed claim, and the
        # lighter verification that replaces it; fully loaded cost per hour of a case officer
        "hours_saved": tri(1.0, 2.5, 4.0, n),
        "hours_verify": RNG.uniform(0.25, 0.75, n),
        "cost_per_hour": RNG.uniform(55, 80, n),
        # DATA-anchored: scam complaints that reach AFCA / scam-and-fraud IDR complaints (FY26),
        # scaled down because small claims escalate less often (ASSUMPTION factor 0.3-0.8)
        "escalation": base["scam_escalation_rate"] * RNG.uniform(0.3, 0.8, n),
        # DATA: share of bank complaints AFCA closed at registration & referral (FY26, peer banks)
        "afca_ref_share": np.full(n, base["afca_closed_at_referral_share"]),
        # DATA-anchored: median of today's IDR scam remedies (used to estimate how much of
        # today's spend already sits in sub-$3,000 payments). Mean is DATA ($1,973 FY26).
        "remedy_median": RNG.uniform(400, 650, n),
    }


def lognormal_params(mean, median):
    sigma = np.sqrt(2 * np.log(np.maximum(mean / median, 1.0001)))
    return np.log(median), sigma


def partial_expectation(mu, sigma, k):
    """E[L * 1(L < k)] for L ~ LogNormal(mu, sigma)."""
    return np.exp(mu + sigma ** 2 / 2) * stats.norm.cdf((np.log(k) - mu - sigma ** 2) / sigma)


def simulate(inp: dict, base: dict, share: float = 1.0, current_remedies: float | None = None,
             threshold: float = THRESHOLD) -> pd.DataFrame:
    current_remedies = base["idr_remedies_fy26"] if current_remedies is None else current_remedies
    mu, sigma = lognormal_params(inp["mean_loss"], inp["median_loss"])
    claims = inp["n0"] * share * (1 + inp["growth"]) ** YEARS_AHEAD * inp["uptake"]
    verified = claims * inp["verified"]
    p_small = stats.norm.cdf((np.log(threshold) - mu) / sigma)
    pe_small = partial_expectation(mu, sigma, threshold)
    eligible = verified * p_small
    gross = verified * pe_small                                    # auto-reimbursed dollars
    # how much of today's IDR scam remedy spend is already in payments under the threshold
    r_mu, r_sigma = lognormal_params(base["idr_avg_remedy"], inp["remedy_median"])
    already_paid = current_remedies * stats.norm.cdf((np.log(threshold) - r_mu - r_sigma ** 2) / r_sigma)
    ops_saving = eligible * (inp["hours_saved"] - inp["hours_verify"]) * inp["cost_per_hour"]
    fee = (inp["afca_ref_share"] * AFCA_FEES["registration_referral"]
           + (1 - inp["afca_ref_share"]) * (AFCA_FEES["case_mgmt_fast_track"] + AFCA_FEES["case_mgmt_standard"]) / 2
           ) * AFCA_FY26_UPLIFT
    afca_saving = eligible * inp["escalation"] * fee
    incremental = gross - already_paid
    net = incremental - ops_saving - afca_saving
    return pd.DataFrame({
        "claims": claims, "eligible_claims": eligible, "share_claims_eligible": eligible / verified,
        "gross_reimbursement": gross, "already_paid_today": already_paid,
        "incremental_reimbursement": incremental, "ops_saving": ops_saving, "afca_fee_saving": afca_saving,
        "net_cost": net, "share_of_loss_dollars_under_threshold": pe_small / inp["mean_loss"],
        "loss_dollars_above_threshold": verified * (inp["mean_loss"] - pe_small),
    })


def summarise(sim: pd.DataFrame) -> pd.DataFrame:
    return sim.quantile([0.1, 0.5, 0.9]).T.rename(columns={0.1: "P10", 0.5: "P50", 0.9: "P90"})


def base_inputs(con) -> dict:
    f = json.loads((PROCESSED / "findings.json").read_text())
    afca = q(con, """SELECT SUM(closed_at_referral)::DOUBLE / SUM(complaints_received) s
                     FROM afca_banks WHERE fy = 'FY2026'""")["s"][0]
    # AFCA banking & finance scam complaints FY2025-26 = 6,580 (AFCA preliminary FY26 figures as
    # reported by Insurance Business, 22 Oct 2026) / IDR scam & fraud complaints FY26 (ASIC)
    scam_escalation = 6_580 / f["q2"]["scam_fraud_fy26"]
    return {
        "afcx_reports_with_loss": TSR["afcx_2025"]["reports_with_loss"],
        "afcx_mean_loss": TSR["afcx_2025"]["loss"] / TSR["afcx_2025"]["reports_with_loss"],
        "idr_remedies_fy26": f["q4"]["idr_scam_remedies_paid_fy26"],
        "idr_avg_remedy": f["q4"]["idr_scam_avg_remedy_fy26"],
        "scam_escalation_rate": scam_escalation,
        "afca_closed_at_referral_share": float(afca),
    }


def bank_shares(con) -> pd.DataFrame:
    # Default allocation: each bank's share of peer-bank Scams/fraud IDR complaints (FY26).
    # Because banks code scam complaints differently (see Q3), a second allocation by share of
    # ALL IDR complaints is kept as a sensitivity check.
    s = q(con, """SELECT bank, tier, SUM(scam_fraud_complaints) scam_fraud, SUM(total_complaints) all_complaints
                  FROM v_bank_scam_half WHERE half IN ('2025 HY2', '2026 HY1') GROUP BY ALL""")
    s["share"] = s.scam_fraud / s.scam_fraud.sum()
    s["share_alt"] = s.all_complaints / s.all_complaints.sum()
    rem = pd.read_csv(OUT / "q4_bank_remedies_fy26.csv")[["bank", "paid"]]
    return s.merge(rem, on="bank", how="left").fillna({"paid": 0}).sort_values("share", ascending=False)


def swing(base: dict, inp: dict) -> pd.DataFrame:
    """One-at-a-time: hold every input at its median, move one to its P10 and P90."""
    med = {k: np.full(1, np.median(v)) for k, v in inp.items()}
    centre = simulate(med, base)["net_cost"][0]
    rows = []
    for k, v in inp.items():
        if np.ptp(v) == 0:
            continue
        lo, hi = np.quantile(v, [0.1, 0.9])
        a = simulate({**med, k: np.full(1, lo)}, base)["net_cost"][0]
        b = simulate({**med, k: np.full(1, hi)}, base)["net_cost"][0]
        rows.append({"input": k, "low_value": lo, "high_value": hi, "net_at_low": a, "net_at_high": b,
                     "swing": abs(b - a)})
    return pd.DataFrame(rows).sort_values("swing", ascending=False), centre


LABELS = {"median_loss": "Median scam loss ($400-$1,000)", "mean_loss": "Mean scam loss (+/-15%)",
          "uptake": "Extra claims from auto-refund (x1.0-1.5)", "growth": "Annual growth in scam losses",
          "verified": "Share of claims verified (60-95%)", "hours_saved": "Investigation hours avoided",
          "cost_per_hour": "Case-officer cost per hour", "hours_verify": "Verification hours per claim",
          "escalation": "AFCA escalation rate of small claims", "remedy_median": "Median of today's remedies"}


def charts(sim: pd.DataFrame, sw: pd.DataFrame, centre: float, curve: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ax.hist(sim.net_cost / 1e6, bins=80, color=style.BLUE, edgecolor=style.SURFACE, linewidth=0.3)
    for p, lab in zip(np.quantile(sim.net_cost / 1e6, [0.1, 0.5, 0.9]), ["P10", "P50", "P90"]):
        ax.axvline(p, color=style.INK, lw=0.9)
        ax.text(p, ax.get_ylim()[1] * 0.97, f" {lab} ${p:,.0f}m", fontsize=9, va="top")
    ax.set_xlabel("Net extra cost to the banking industry in FY2028, $ million")
    ax.grid(axis="x", visible=False); ax.set_yticks([])
    ax.set_title("Auto-reimbursing scam losses under $3,000: likely net cost")
    style.subtitle(ax, "100,000 simulations; extra refunds minus today's remedies, investigation time and AFCA fees avoided")
    style.source(fig, "Model in src/04_spf_model.py; inputs from NASC TSR 2025, ASIC IDR, AFCA Datacube and fee guide, plus labelled assumptions.")
    style.save(fig, FIG / "f8_spf_net_cost.png")

    top = sw.head(8).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 4))
    for i, r in enumerate(top.itertuples()):
        lo, hi = sorted([r.net_at_low, r.net_at_high])
        ax.barh(i, (hi - lo) / 1e6, left=lo / 1e6, color=style.BLUE, height=0.55)
    ax.axvline(centre / 1e6, color=style.INK, lw=0.9)
    ax.set_yticks(range(len(top)), [LABELS.get(k, k) for k in top.input])
    ax.set_xlabel("Net cost in FY2028, $ million (bar = input moved from its P10 to its P90)")
    ax.grid(axis="y", visible=False)
    ax.set_title("What the answer depends on")
    style.subtitle(ax, f"Swing analysis around the median case (${centre/1e6:,.0f}m)")
    style.source(fig, "src/04_spf_model.py, one-at-a-time sensitivity.")
    style.save(fig, FIG / "f9_swing.png")

    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ax.plot(curve.threshold, curve.claims_share * 100, color=style.BLUE, lw=2, marker="o", ms=5)
    ax.plot(curve.threshold, curve.dollar_share * 100, color=style.ORANGE, lw=2, marker="o", ms=5)
    ax.text(curve.threshold.iloc[-1] + 150, curve.claims_share.iloc[-1] * 100, "% of claims covered", va="center", fontsize=9)
    ax.text(curve.threshold.iloc[-1] + 150, curve.dollar_share.iloc[-1] * 100, "% of loss dollars covered", va="center", fontsize=9)
    ax.axvline(3000, color=style.INK_2, lw=0.8)
    ax.text(3050, 3, "proposed $3,000", fontsize=8.5, color=style.INK_2)
    ax.set_xlim(0, 12500); ax.set_ylim(0, 100)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.set_xlabel("Auto-reimbursement threshold")
    ax.set_title("A $3,000 cap covers most victims but a minority of the money")
    style.subtitle(ax, "Median across simulations, %")
    style.source(fig, "src/04_spf_model.py; loss distribution anchored to AFCX mean and Scamwatch / IDR medians.")
    style.save(fig, FIG / "f10_threshold_curve.png")


def main() -> None:
    con = connect()
    base = base_inputs(con)
    inp = build_inputs(N_DRAWS, base)
    sim = simulate(inp, base)
    summ = summarise(sim)
    summ.to_csv(OUT / "q7_spf_industry_summary.csv")

    shares = bank_shares(con)
    rows = []
    for r in shares.itertuples():
        b = summarise(simulate(inp, base, share=r.share, current_remedies=r.paid))
        alt = simulate(inp, base, share=r.share_alt, current_remedies=r.paid)["net_cost"].median()
        rows.append({"bank": r.bank, "tier": r.tier, "share_of_bank_scam_complaints": r.share,
                     "share_of_all_complaints": r.share_alt, "net_cost_P50_alt_allocation": alt,
                     "idr_scam_remedies_fy26": r.paid,
                     **{f"{m}_{p}": b.loc[m, p] for m in ["eligible_claims", "gross_reimbursement",
                                                           "incremental_reimbursement", "ops_saving",
                                                           "afca_fee_saving", "net_cost"]
                        for p in ["P10", "P50", "P90"]}})
    banks = pd.DataFrame(rows)
    banks.to_csv(OUT / "q7_spf_by_bank.csv", index=False)

    sw, centre = swing(base, inp)
    sw.to_csv(OUT / "q7_swing.csv", index=False)

    curve = []
    for t in [500, 1000, 2000, 3000, 5000, 7500, 10000]:
        s = simulate(inp, base, threshold=t)
        curve.append({"threshold": t, "claims_share": s.share_claims_eligible.median(),
                      "dollar_share": s.share_of_loss_dollars_under_threshold.median(),
                      "gross_reimbursement_p50": s.gross_reimbursement.median()})
    curve = pd.DataFrame(curve)
    curve.to_csv(OUT / "q7_threshold_curve.csv", index=False)
    charts(sim, sw, centre, curve)

    out = {"inputs": base, "industry": summ.round(3).to_dict(orient="index"),
           "p_net_cost_positive": float((sim.net_cost > 0).mean()),
           "swing_top3": sw.head(3)[["input", "swing"]].to_dict(orient="records")}
    (PROCESSED / "spf_model.json").write_text(json.dumps(out, indent=2, default=float))
    pd.set_option("display.float_format", lambda v: f"{v:,.2f}")
    print(summ)
    print(banks[["bank", "share_of_bank_scam_complaints", "net_cost_P10", "net_cost_P50", "net_cost_P90"]])
    print(sw[["input", "swing"]])
    print(curve)
    print("P(net cost > 0):", out["p_net_cost_positive"], "\nbase:", base)


if __name__ == "__main__":
    main()
