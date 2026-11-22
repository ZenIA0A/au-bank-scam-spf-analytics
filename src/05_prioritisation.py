"""Step 5 - Which scam controls should a bank fund first?

Auto-reimbursement only covers losses under $3,000 (about 13% of loss dollars - see step 4),
so most of the money is in larger scams that prevention must stop. This step ranks six
controls named in the draft SPF bank code, using a transparent value-vs-effort framework:

  avoided loss  = loss pool the control targets (DATA, NASC 2025 combined losses by scam type)
                  x share of bank-reported losses (DATA, AFCX $842.3m / $2.18b combined)
                  x effectiveness (ASSUMPTION range, sampled 20,000 times)
  priority      = avoided loss / effort score (effort and customer friction are 1-5 judgements)

The output is a ranking WITH uncertainty: the probability each control lands in the top 3,
plus a pilot design (sample size) to replace the effectiveness assumptions with evidence.

Run:  python src/05_prioritisation.py
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

import style
from config import FIG, OUT, PROCESSED, TSR

style.apply()
RNG = np.random.default_rng(7)
N = 20_000
pools = TSR["combined_loss_by_type_2025"]
BANK_SHARE = TSR["afcx_2025"]["loss"] / TSR["combined_loss_by_year"][2025]  # share of losses that reach banks' own reporting

# Each control targets one scam-type pool so that pools are not double counted.
CONTROLS = [
    {"control": "Confirmation of Payee on new payees", "pool": "Payment redirection", "eff": (0.25, 0.50),
     "effort": 3, "friction": 1,
     "why": "Name/account mismatch is the core of invoice and payment-redirection scams"},
    {"control": "Holds & limits on first-time high-risk payments (crypto exchanges, new high-value payees)",
     "pool": "Investment", "eff": (0.10, 0.30), "effort": 3, "friction": 4,
     "why": "Investment scams are 38% of losses; crypto exchanges and bank transfers carry 91% of Scamwatch losses with a known payment method"},
    {"control": "Behavioural scam-detection model with call-back (repeated payments to new beneficiaries)",
     "pool": "Romance", "eff": (0.10, 0.30), "effort": 4, "friction": 2,
     "why": "Romance scams build through many payments over weeks - a pattern a model can learn"},
    {"control": "Remote-access tool and session-risk detection in digital banking", "pool": "Remote access",
     "eff": (0.30, 0.60), "effort": 2, "friction": 1,
     "why": "Remote-access losses already fell 34% in 2025, which NASC attributes partly to bank and telco disruption"},
    {"control": "Real-time scam intelligence sharing and phishing-site takedown", "pool": "Phishing",
     "eff": (0.10, 0.25), "effort": 2, "friction": 1,
     "why": "SPF principle 4 requires actionable scam intelligence to be reported and shared"},
    {"control": "Mule-account detection and blocking (receiving side)", "pool": "Other",
     "eff": (0.03, 0.10), "effort": 4, "friction": 1,
     "why": "Applies across all scam types; low per-type effect but the largest pool ($872m)"},
]


def main() -> None:
    rows, draws = [], {}
    for c in CONTROLS:
        pool_bank = pools[c["pool"]] * BANK_SHARE
        eff = RNG.uniform(*c["eff"], N)
        avoided = pool_bank * eff
        draws[c["control"]] = avoided / c["effort"]
        rows.append({**{k: v for k, v in c.items() if k != "eff"},
                     "eff_low": c["eff"][0], "eff_high": c["eff"][1],
                     "pool_combined": pools[c["pool"]], "pool_bank_reported": pool_bank,
                     "avoided_P10": np.quantile(avoided, 0.1), "avoided_P50": np.median(avoided),
                     "avoided_P90": np.quantile(avoided, 0.9)})
    df = pd.DataFrame(rows)
    score = pd.DataFrame(draws)
    ranks = score.rank(axis=1, ascending=False)
    df["p_top3"] = df.control.map((ranks <= 3).mean())
    df["median_rank"] = df.control.map(ranks.median())
    df["priority_P50"] = df.avoided_P50 / df.effort
    df = df.sort_values("priority_P50", ascending=False).reset_index(drop=True)
    df.to_csv(OUT / "q8_control_priorities.csv", index=False)

    # Pilot design for the top-ranked friction control: randomised hold-out on flagged payments.
    power = NormalIndPower()
    pilot = []
    for p0 in [0.005, 0.01, 0.02]:
        for rel in [0.20, 0.30]:
            es = proportion_effectsize(p0, p0 * (1 - rel))
            n = power.solve_power(effect_size=abs(es), alpha=0.05, power=0.8, ratio=1.0)
            pilot.append({"baseline_scam_rate": p0, "relative_reduction": rel, "n_per_arm": int(np.ceil(n))})
    pilot = pd.DataFrame(pilot)
    pilot.to_csv(OUT / "q8_pilot_sample_size.csv", index=False)

    # Value vs effort chart
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    short = {
        "Confirmation of Payee on new payees": "Confirmation of Payee",
        "Holds & limits on first-time high-risk payments (crypto exchanges, new high-value payees)": "High-risk payment holds & limits",
        "Behavioural scam-detection model with call-back (repeated payments to new beneficiaries)": "Behavioural detection model",
        "Remote-access tool and session-risk detection in digital banking": "Remote-access detection",
        "Real-time scam intelligence sharing and phishing-site takedown": "Intelligence sharing & takedown",
        "Mule-account detection and blocking (receiving side)": "Mule-account blocking",
    }
    for r in df.itertuples():
        top = r.Index == 0
        ax.errorbar(r.effort, r.avoided_P50 / 1e6,
                    yerr=[[(r.avoided_P50 - r.avoided_P10) / 1e6], [(r.avoided_P90 - r.avoided_P50) / 1e6]],
                    fmt="o", ms=9, color=style.BLUE if top else style.INK_2, ecolor=style.MUTED, elinewidth=2, capsize=0)
        ax.annotate(short[r.control], (r.effort, r.avoided_P50 / 1e6), xytext=(10, 0), textcoords="offset points",
                    va="center", fontsize=9, color=style.INK)
    ax.set_xlim(1.5, 5.2); ax.set_xticks([2, 3, 4], ["2 - lower effort", "3", "4 - higher effort"])
    ax.set_ylabel("Avoided bank-reported losses per year, $m")
    ax.set_title("Holds on high-risk payments and Confirmation of Payee give the most per unit of effort")
    style.subtitle(ax, "Dot = median, line = P10-P90 from effectiveness ranges. Effort is a 1-5 judgement")
    style.source(fig, "Loss pools: NASC TSR 2025 combined losses by type x AFCX share of losses. Effectiveness and effort: labelled assumptions in src/05_prioritisation.py.")
    style.save(fig, FIG / "f11_control_priorities.png")

    (PROCESSED / "priorities.json").write_text(json.dumps(
        {"bank_share_of_losses": BANK_SHARE, "ranking": df[["control", "avoided_P50", "p_top3", "median_rank"]].to_dict(orient="records"),
         "pilot": pilot.to_dict(orient="records")}, indent=2, default=float))
    pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 60)
    print(df[["control", "pool", "avoided_P10", "avoided_P50", "avoided_P90", "effort", "friction", "priority_P50", "p_top3"]])
    print(pilot)


if __name__ == "__main__":
    main()
