"""Streamlit dashboard: SPF scam-reimbursement readiness.

Run from the repo root after `python run_all.py`:
    streamlit run app/streamlit_app.py

The model tab re-runs the same Monte Carlo as src/04_spf_model.py, with the assumption
ranges exposed as controls, so a user can test their own view of the inputs.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TABLES = ROOT / "reports" / "tables"
sys.path.insert(0, str(SRC))
spec = importlib.util.spec_from_file_location("spf_model", SRC / "04_spf_model.py")
spf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spf)

BLUE, ORANGE, GREY, INK2 = "#2a78d6", "#eb6834", "#b9b7b0", "#52514e"
st.set_page_config(page_title="SPF scam reimbursement readiness", layout="wide")


@st.cache_data
def load():
    t = {p.stem: pd.read_csv(p) for p in TABLES.glob("*.csv")}
    f = json.loads((ROOT / "data" / "processed" / "findings.json").read_text())
    m = json.loads((ROOT / "data" / "processed" / "spf_model.json").read_text())
    return t, f, m


T, F, M = load()
base = M["inputs"]


def fmt_m(x):
    return f"${x/1e6:,.1f}m"


st.title("Scams Prevention Framework: what auto-reimbursement will cost banks, and where to act first")
st.caption("Independent analysis on public data: ASIC IDR (Jul 2023 - Jun 2026), AFCA Datacube (FY25-26), "
           "NASC Targeting Scams Report 2025. Author: James Lai.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Scam losses reported, 2025", "$2.18b", "+7.8% vs 2024", delta_color="inverse")
c2.metric("Bank-reported scam losses, 2025", fmt_m(842.3e6), f"{base['afcx_reports_with_loss']:,} reports", delta_color="off")
c3.metric("Money returned via IDR, FY26", fmt_m(F["q4"]["idr_scam_remedies_paid_fy26"]),
          f"{F['q4']['paid_vs_afcx_loss_ratio']:.1%} of bank-reported losses", delta_color="off")
c4.metric("Net cost of $3k auto-refund, FY2028 (P50)", fmt_m(M["industry"]["net_cost"]["P50"]),
          f"P10 {fmt_m(M['industry']['net_cost']['P10'])} - P90 {fmt_m(M['industry']['net_cost']['P90'])}", delta_color="off")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Scam losses", "Complaints today", "Cost model", "Where to act", "Data & assumptions"])

# ---------------------------------------------------------------- tab 1
with tab1:
    a, b = st.columns(2)
    yr = T["q1_losses_by_year"]
    fig = px.bar(yr, x=yr.year.astype(str), y=yr.loss / 1e9, labels={"x": "", "y": "$ billion"},
                 title="Combined reported scam losses", color_discrete_sequence=[BLUE])
    fig.update_traces(hovertemplate="%{x}: $%{y:.2f}b<extra></extra>")
    a.plotly_chart(fig, width='stretch')
    bt = T["q1_losses_by_type"].rename(columns={"Unnamed: 0": "type"}).sort_values("loss_2025")
    fig = px.bar(bt, y="type", x=bt.loss_2025 / 1e6, orientation="h", title="Losses by scam type, 2025 ($m)",
                 color=bt.type.eq("Investment").map({True: "Investment", False: "Other types"}),
                 color_discrete_map={"Investment": BLUE, "Other types": GREY},
                 labels={"x": "$ million", "type": "", "color": ""})
    b.plotly_chart(fig, width='stretch')
    a, b = st.columns(2)
    pm = T["q1_scamwatch_payment_method"].rename(columns={"Unnamed: 0": "method"}).sort_values("loss")
    a.plotly_chart(px.bar(pm, y="method", x=pm.loss / 1e6, orientation="h", color_discrete_sequence=[BLUE],
                          title="Scamwatch losses by payment method, 2025 ($m)", labels={"x": "$ million", "method": ""}),
                   width='stretch')
    cm = T["q1_scamwatch_contact_method"].rename(columns={"Unnamed: 0": "channel"}).sort_values("loss_per_report")
    b.plotly_chart(px.bar(cm, y="channel", x="loss_per_report", orientation="h", color_discrete_sequence=[BLUE],
                          title="Average loss per report by first contact ($)", labels={"loss_per_report": "$", "channel": ""}),
                   width='stretch')

# ---------------------------------------------------------------- tab 2
with tab2:
    tr = T["q2_idr_trend"]
    fig = go.Figure()
    fig.add_scatter(x=tr.half, y=tr.all_complaints_idx, name="All IDR complaints", line=dict(color=GREY, width=2))
    fig.add_scatter(x=tr.half, y=tr.scam_fraud_idx, name="Scam & fraud complaints", line=dict(color=BLUE, width=2))
    fig.update_layout(title="IDR complaints, index 2023 HY2 = 100", yaxis_title="Index", hovermode="x unified")
    st.plotly_chart(fig, width='stretch')

    st.subheader("Each major bank labels scam complaints differently")
    mix = T["q3_major_bank_scam_issue_mix"].melt(id_vars=["bank", "half"], var_name="issue", value_name="share")
    fig = px.bar(mix, x="half", y="share", color="issue", facet_col="bank", facet_col_wrap=4,
                 color_discrete_sequence=[ORANGE, "#1baf7a", "#eda100", BLUE],
                 category_orders={"bank": ["CBA", "NAB", "ANZ", "Westpac"]})
    fig.update_yaxes(tickformat=".0%"); fig.update_layout(legend=dict(orientation="h", y=-0.25), height=420)
    st.plotly_chart(fig, width='stretch')

    a, b = st.columns(2)
    rem = T["q4_scam_remedies_total"]
    a.plotly_chart(px.bar(rem, x="half", y=rem.amount_paid / 1e6, color_discrete_sequence=[BLUE],
                          title="Monetary remedies on scam & fraud complaints ($m per half-year)",
                          labels={"y": "$ million", "half": ""}), width='stretch')
    esc = T["q6_escalation_fy26"].sort_values("escalation_rate")
    fig = px.bar(esc, y="bank", x=esc.escalation_rate * 100, orientation="h", color="tier",
                 color_discrete_map={"Major bank": BLUE, "Other bank": GREY, "Digital/neo": ORANGE},
                 title="Complaints reaching AFCA per 100 IDR complaints, FY26", labels={"x": "%", "bank": ""})
    b.plotly_chart(fig, width='stretch')
    st.dataframe(T["q4_bank_remedies_fy26"].rename(columns={"paid": "paid_$", "scam_fraud": "scam_fraud_complaints"}),
                 hide_index=True, width='stretch')

# ---------------------------------------------------------------- tab 3
with tab3:
    st.markdown("Treasury proposes that verified scam losses **under a threshold** are refunded automatically. "
                "Move the controls to test your own assumptions; the model re-runs 20,000 simulations.")
    left, right = st.columns([1, 2])
    with left:
        banks = T["q7_spf_by_bank"]
        who = st.selectbox("Scope", ["Banking industry"] + banks.bank.tolist())
        alloc = st.radio("Allocate bank volume by", ["Share of scam/fraud complaints", "Share of all complaints"],
                         help="Banks code scam complaints differently, so two allocations are shown.")
        thr = st.select_slider("Auto-refund threshold ($)", [500, 1000, 2000, 3000, 5000, 7500, 10000], value=3000)
        g = st.slider("Annual growth in scam losses to FY2028", -0.15, 0.25, (-0.10, 0.15), 0.01)
        up = st.slider("Extra claims caused by auto-refunds (x)", 1.0, 2.0, (1.0, 1.5), 0.05)
        ver = st.slider("Share of claims verified", 0.4, 1.0, (0.60, 0.95), 0.05)
        med = st.slider("Median scam loss ($)", 200, 2000, (400, 1000), 50)
        hrs = st.slider("Investigation hours avoided per auto-refund", 0.5, 6.0, (1.0, 4.0), 0.5)
    n = 20_000
    rng = np.random.default_rng(1)
    inp = {
        "n0": np.full(n, base["afcx_reports_with_loss"]),
        "growth": rng.triangular(g[0], (g[0] + g[1]) / 2, g[1], n),
        "uptake": rng.triangular(up[0], (up[0] + up[1]) / 2, up[1], n),
        "mean_loss": base["afcx_mean_loss"] * rng.uniform(0.85, 1.15, n),
        "median_loss": rng.uniform(med[0], med[1], n),
        "verified": rng.triangular(ver[0], (ver[0] + ver[1]) / 2, ver[1], n),
        "hours_saved": rng.triangular(hrs[0], (hrs[0] + hrs[1]) / 2, hrs[1], n),
        "hours_verify": rng.uniform(0.25, 0.75, n),
        "cost_per_hour": rng.uniform(55, 80, n),
        "escalation": base["scam_escalation_rate"] * rng.uniform(0.3, 0.8, n),
        "afca_ref_share": np.full(n, base["afca_closed_at_referral_share"]),
        "remedy_median": rng.uniform(400, 650, n),
    }
    if who == "Banking industry":
        share, cur = 1.0, base["idr_remedies_fy26"]
    else:
        row = banks[banks.bank == who].iloc[0]
        share = row.share_of_bank_scam_complaints if alloc.startswith("Share of scam") else row.share_of_all_complaints
        cur = row.idr_scam_remedies_fy26
    sim = spf.simulate(inp, base, share=share, current_remedies=cur, threshold=float(thr))
    q = sim.quantile([0.1, 0.5, 0.9])
    with right:
        k1, k2, k3 = st.columns(3)
        k1.metric("Claims refunded automatically (P50)", f"{q.eligible_claims[0.5]:,.0f}",
                  f"{q.share_claims_eligible[0.5]:.0%} of verified claims", delta_color="off")
        k2.metric("Net extra cost (P50)", fmt_m(q.net_cost[0.5]),
                  f"P10 {fmt_m(q.net_cost[0.1])} - P90 {fmt_m(q.net_cost[0.9])}", delta_color="off")
        k3.metric("Loss dollars covered", f"{q.share_of_loss_dollars_under_threshold[0.5]:.0%}",
                  f"{fmt_m(q.loss_dollars_above_threshold[0.5])} stays above threshold", delta_color="off")
        fig = px.histogram(sim.net_cost / 1e6, nbins=70, color_discrete_sequence=[BLUE])
        for p in [0.1, 0.5, 0.9]:
            fig.add_vline(q.net_cost[p] / 1e6, line_color="#0b0b0b", line_width=1,
                          annotation_text=f"P{int(p*100)} {fmt_m(q.net_cost[p])}")
        fig.update_layout(showlegend=False, title=f"Net extra cost in FY2028 - {who}", xaxis_title="$ million",
                          yaxis_title="Simulations")
        st.plotly_chart(fig, width='stretch')
        wf = pd.DataFrame({"step": ["Auto-refunds", "Already paid today", "Investigation time avoided", "AFCA fees avoided", "Net cost"],
                           "value": [q.gross_reimbursement[0.5], -q.already_paid_today[0.5], -q.ops_saving[0.5],
                                     -q.afca_fee_saving[0.5], q.net_cost[0.5]]})
        fig = go.Figure(go.Waterfall(x=wf.step, y=wf.value / 1e6, measure=["relative"] * 4 + ["total"],
                                     increasing=dict(marker_color=ORANGE), decreasing=dict(marker_color=BLUE),
                                     totals=dict(marker_color=INK2)))
        fig.update_layout(title="How the P50 net cost builds up ($m; medians, so steps do not sum exactly)")
        st.plotly_chart(fig, width='stretch')

# ---------------------------------------------------------------- tab 4
with tab4:
    pr = T["q8_control_priorities"]
    fig = px.scatter(pr, x="effort", y=pr.avoided_P50 / 1e6, text="pool", size=[18] * len(pr),
                     error_y=(pr.avoided_P90 - pr.avoided_P50) / 1e6, error_y_minus=(pr.avoided_P50 - pr.avoided_P10) / 1e6,
                     hover_name="control", color_discrete_sequence=[BLUE],
                     labels={"effort": "Effort (1-5 judgement)", "y": "Avoided bank-reported losses, $m / year"},
                     title="Value vs effort of SPF controls (dot = P50, bar = P10-P90)")
    fig.update_traces(textposition="middle right")
    st.plotly_chart(fig, width='stretch')
    show = pr[["control", "pool", "avoided_P50", "effort", "friction", "p_top3", "why"]].copy()
    show["avoided_P50"] = (show.avoided_P50 / 1e6).round(1)
    show["p_top3"] = (show.p_top3 * 100).round(0).astype(int).astype(str) + "%"
    st.dataframe(show.rename(columns={"avoided_P50": "avoided $m (P50)", "p_top3": "P(top 3)"}),
                 hide_index=True, width='stretch')
    st.subheader("Pilot sample size for a randomised hold-out")
    st.dataframe(T["q8_pilot_sample_size"], hide_index=True)

# ---------------------------------------------------------------- tab 5
with tab5:
    st.markdown("**Data-quality checks** (`src/02_quality_checks.py`)")
    st.dataframe(T["data_quality"], hide_index=True, width='stretch')
    st.markdown("**Swing analysis** - how far the industry net cost moves when each input goes from its P10 to its P90")
    st.dataframe(T["q7_swing"], hide_index=True, width='stretch')
    st.markdown("Full assumptions register: `docs/07_assumptions_register.md`. Sources: ASIC IDR data file (16 Nov 2026); "
                "AFCA Datacube; NASC Targeting Scams Report 2025; AFCA Complaint Fee Guide; Treasury SPF IDR position paper (May 2026).")
