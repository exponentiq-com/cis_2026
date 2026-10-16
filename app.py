# -*- coding: utf-8 -*-
"""
CIS 2026 (10 Countries) — client dashboard
Country comparison with optional demographic filters.
"""
from __future__ import annotations

import hmac
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from demographics import (
    AGE_ORDER,
    COUNTRY_ORDER,
    EDU_ORDER,
    GENDER_ORDER,
    INCOME_ORDER,
    URBAN_ORDER,
    legend_pairs_from_fig,
    ordered_present,
    render_demographic_profiles,
    render_html_legend,
)
from questions import QUESTIONS, resolve_order, sections

DATA_PATH = Path(__file__).resolve().parent / "data" / "cis2026.parquet"

# Natural palette — slate / teal / warm stone (avoid neon / purple “AI” look)
COLORS = {
    "ink": "#1F2A2E",
    "slate": "#3D4F56",
    "teal": "#2F6F6A",
    "teal_soft": "#5B8F89",
    "sand": "#E7E2D8",
    "paper": "#F7F5F1",
    "line": "#8A6A3B",
    "grid": "#D9D3C7",
    "countries": [
        "#2F6F6A",
        "#3D5A80",
        "#8A6A3B",
        "#6B7F5A",
        "#7A4E3A",
        "#4A6FA5",
        "#5C6B73",
        "#9C6644",
        "#3F6B5A",
        "#6E5A7B",
    ],
}

st.set_page_config(
    page_title="Country Image Study 2026",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@500;600;700&family=Source+Sans+3:wght@400;500;600&display=swap');

      html, body, [class*="css"] {{
        font-family: "Source Sans 3", "Segoe UI", sans-serif;
      }}
      .stApp {{ background-color: {COLORS["paper"]}; color: {COLORS["ink"]}; }}
      h1, h2, h3 {{
        font-family: "Source Serif 4", Georgia, serif !important;
        color: {COLORS["ink"]} !important;
        font-weight: 600 !important;
      }}
      .block-container {{
        padding-top: 1.6rem;
        padding-bottom: 2.2rem;
        max-width: 1180px;
      }}

      /* Sidebar */
      [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #EDE7DC 0%, #E4DDD1 100%);
        border-right: 1px solid {COLORS["grid"]};
      }}
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: {COLORS["slate"]};
      }}
      .side-brand {{
        font-family: "Source Serif 4", Georgia, serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: {COLORS["ink"]};
        line-height: 1.25;
        margin: 0.15rem 0 0.1rem 0;
      }}
      .side-brand-sub {{
        font-size: 0.78rem;
        color: {COLORS["slate"]};
        margin-bottom: 0.85rem;
        letter-spacing: 0.02em;
      }}
      .side-rule {{
        border: none;
        border-top: 1px solid #C9C1B4;
        margin: 0.7rem 0 0.9rem 0;
      }}

      /* Quiet chrome — do not hide header (sidebar toggles live there in 1.65) */
      #MainMenu {{ visibility: hidden; }}
      footer {{ visibility: hidden; }}
      header[data-testid="stHeader"] {{
        background: transparent;
        height: 3rem;
      }}
      /* Hide only the Deploy button, keep header toggles */
      [data-testid="stToolbar"] [data-testid="stAppDeployButton"],
      .stDeployButton {{
        display: none !important;
      }}

      /* CLOSE: always show collapse control in the sidebar (not hover-only) */
      [data-testid="stSidebarHeader"],
      [data-testid="stSidebarCollapseButton"],
      [data-testid="stSidebarCollapseButton"] button {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
      }}
      [data-testid="stSidebarCollapseButton"] {{
        z-index: 1000002 !important;
      }}

      /* OPEN: when sidebar is collapsed, force expand control visible */
      [data-testid="stHeader"] [data-testid="stExpandSidebarButton"],
      [data-testid="stExpandSidebarButton"],
      [data-testid="stSidebarCollapsedControl"],
      [data-testid="collapsedControl"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        z-index: 1000002 !important;
        position: fixed !important;
        left: 0.45rem !important;
        top: 0.55rem !important;
        background: #FFFFFF !important;
        border: 1px solid {COLORS["grid"]} !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 4px rgba(31,42,46,0.14) !important;
      }}
      [data-testid="stExpandSidebarButton"] svg,
      [data-testid="stSidebarCollapseButton"] svg,
      [data-testid="stSidebarCollapsedControl"] svg {{
        fill: {COLORS["ink"]} !important;
      }}

      div[data-testid="stMetric"] {{
        background: #FFFFFF;
        border: 1px solid {COLORS["grid"]};
        border-left: 3px solid {COLORS["teal"]};
        padding: 0.75rem 0.9rem;
        border-radius: 2px;
        box-shadow: none;
      }}
      div[data-testid="stMetric"] label {{ color: {COLORS["slate"]} !important; }}

      .cis-title {{
        font-family: "Source Serif 4", Georgia, serif;
        font-size: 1.55rem;
        letter-spacing: 0.01em;
        line-height: 1.25;
        margin-bottom: 0.2rem;
        color: {COLORS["ink"]};
      }}
      .cis-sub {{
        color: {COLORS["slate"]};
        font-size: 0.95rem;
        margin-bottom: 1.1rem;
        max-width: 46rem;
      }}
      .cis-qbox {{
        background: #FFFFFF;
        border: 1px solid {COLORS["grid"]};
        border-left: 2px solid {COLORS["teal"]};
        border-radius: 0;
        padding: 0.95rem 1.15rem;
        margin: 0.6rem 0 1rem 0;
      }}
      .cis-qbox b {{
        font-family: "Source Serif 4", Georgia, serif;
        font-size: 1.05rem;
      }}
      .cis-qbox span {{
        display: block;
        margin-top: 0.35rem;
        color: {COLORS["slate"]};
        font-size: 0.92rem;
        line-height: 1.45;
      }}
      .cis-note {{ color: {COLORS["slate"]}; font-size: 0.86rem; margin-bottom: 0.6rem; }}
      .cis-avg {{
        display: block;
        background: transparent;
        border: none;
        border-left: 2px solid {COLORS["line"]};
        color: {COLORS["ink"]};
        font-size: 0.88rem;
        padding: 0.15rem 0 0.15rem 0.75rem;
        margin: 0.15rem 0 0.85rem 0;
        border-radius: 0;
      }}
      .cis-chart-wrap {{
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 0.2rem 0 0.1rem 0;
        margin-bottom: 0.2rem;
        overflow: visible;
      }}
      .cis-chart-wrap .js-plotly-plot,
      .cis-chart-wrap .plot-container {{
        overflow: visible !important;
      }}
      /* Single hairline — not a white band / box */
      .cis-sep {{
        display: block;
        width: 100%;
        height: 1px;
        margin: 1.25rem 0 1.4rem 0;
        padding: 0;
        border: 0 !important;
        border-top: 0 !important;
        background: {COLORS["grid"]};
        background-color: {COLORS["grid"]};
        opacity: 1;
        box-shadow: none;
      }}
      /* Kill Streamlit/browser default <hr> chrome that looks like a white box */
      hr.cis-sep {{
        border: 0 !important;
        background: {COLORS["grid"]} !important;
        background-color: {COLORS["grid"]} !important;
        color: transparent !important;
      }}
      /* HTML legend — full labels, never SVG-clipped by Plotly */
      .cis-legend {{
        display: flex;
        flex-wrap: wrap;
        align-items: flex-start;
        gap: 0.55rem 1.25rem;
        margin: 0.15rem 0 0.85rem 0;
        padding: 0;
      }}
      .cis-leg-item {{
        display: inline-flex;
        align-items: flex-start;
        gap: 0.45rem;
        max-width: 100%;
        font-size: 0.9rem;
        line-height: 1.35;
        color: {COLORS["ink"]};
      }}
      .cis-leg-swatch {{
        width: 11px;
        height: 11px;
        margin-top: 0.28rem;
        flex: 0 0 11px;
        border-radius: 1px;
      }}
      .cis-leg-text {{
        white-space: normal;
        overflow: visible;
        text-overflow: clip;
        word-break: break-word;
      }}

      .cis-table-wrap {{
        border: 1px solid {COLORS["grid"]};
        border-radius: 0;
        overflow: auto;
        background: #fff;
        margin: 0.4rem 0 0.25rem 0;
      }}
      table.cis-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.92rem;
        color: {COLORS["ink"]};
      }}
      table.cis-table th,
      table.cis-table td {{
        text-align: left !important;
        padding: 0.65rem 0.9rem;
        border-bottom: 1px solid {COLORS["grid"]};
        vertical-align: middle;
      }}
      table.cis-table th {{
        background: #F0EBE3;
        font-weight: 600;
      }}
      table.cis-table tr:last-child td {{
        border-bottom: none;
      }}
      table.cis-table tbody tr:nth-child(even) td {{
        background: #FBF9F5;
      }}

      [data-testid="stSidebar"] .stCheckbox {{
        margin-bottom: -0.35rem;
      }}

      /* Demographic Profiles — study at a glance */
      .glance-head {{
        display: flex;
        align-items: stretch;
        background: #1B3A5F;
        border-radius: 12px 12px 0 0;
        overflow: hidden;
      }}
      .glance-accent {{
        width: 8px;
        background: #C4A035;
        flex: 0 0 8px;
      }}
      .glance-title {{
        color: #fff;
        font-family: "Source Sans 3", "Segoe UI", sans-serif;
        font-weight: 700;
        font-size: 1.15rem;
        padding: 0.7rem 1rem;
      }}
      .glance-kpis {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 0;
        background: #1B3A5F;
        padding: 0.85rem 0.4rem 1rem 0.4rem;
        border-radius: 0 0 12px 12px;
        margin-bottom: 0.75rem;
      }}
      .glance-kpi {{ text-align: center; padding: 0.25rem 0.4rem; }}
      .glance-num {{
        color: #C4A035;
        font-size: 1.55rem;
        font-weight: 700;
        line-height: 1.15;
        font-family: "Source Sans 3", "Segoe UI", sans-serif;
      }}
      .glance-lab {{
        color: #E8EEF4;
        font-size: 0.78rem;
        margin-top: 0.2rem;
      }}
      .glance-region {{
        border-radius: 12px;
        padding: 0.85rem 0.9rem;
        min-height: 7.2rem;
        border: 1px solid {COLORS["grid"]};
      }}
      .glance-region-name {{
        font-weight: 700;
        color: #1B3A5F;
        font-size: 1rem;
        margin-bottom: 0.2rem;
      }}
      .glance-region-n {{
        color: #1B3A5F;
        font-size: 0.9rem;
        margin-bottom: 0.35rem;
      }}
      .glance-region-c {{
        color: {COLORS["slate"]};
        font-size: 0.8rem;
        line-height: 1.35;
      }}
      table.demo-cis-table th {{
        background: #1B3A5F !important;
        color: #fff !important;
      }}
      @media (max-width: 900px) {{
        .glance-kpis {{ grid-template-columns: repeat(2, 1fr); }}
      }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _check_auth() -> bool:
    """Simple sign-in for confidential hosting (set DASHBOARD_USER / DASHBOARD_PASS)."""
    user_ok = os.environ.get("DASHBOARD_USER", "cis2026").strip()
    pass_ok = os.environ.get("DASHBOARD_PASS", "").strip()

    # No password set (local use): open dashboard directly
    if not pass_ok:
        return True

    if st.session_state.get("auth_ok"):
        return True

    st.markdown(
        '<div class="cis-title">A Global Survey on Impression and Understanding of China</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cis-sub">Sign in to view survey results. Access is restricted.</div>',
        unsafe_allow_html=True,
    )
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        if hmac.compare_digest(u.strip(), user_ok) and hmac.compare_digest(p, pass_ok):
            st.session_state["auth_ok"] = True
            st.rerun()
        st.error("Incorrect username or password.")
    return False


@st.cache_data(show_spinner=False)
def load_data(_mtime: float) -> pd.DataFrame:
    """_mtime busts the cache when parquet is rebuilt."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing {DATA_PATH}. Run prepare_parquet.py first."
        )
    df = pd.read_parquet(DATA_PATH)
    # Safety for older cached builds
    if "income_group" not in df.columns:
        df["income_group"] = "Not stated"
    if "city" not in df.columns:
        # Fallback if an older parquet is loaded without s5-derived city
        if "s5" in df.columns:
            df["city"] = df["s5"].astype(str)
        elif "place" in df.columns:
            df["city"] = df["place"].astype(str)
        else:
            df["city"] = "Not stated"
    df["city"] = df["city"].astype(str).replace({"nan": "Not stated", "": "Not stated"})
    if "language" not in df.columns and "s1" in df.columns:
        df["language"] = df["s1"].astype(str)
    if "work_status" not in df.columns and "occupation" in df.columns:
        _nw = {"Housewife", "Student", "Unemployed/ laid off/ retired"}
        df["work_status"] = df["occupation"].map(
            lambda x: "Non-working" if str(x) in _nw else "Working"
        )
    return df


def apply_filters(df: pd.DataFrame, countries, gender, age, urban, edu, income) -> pd.DataFrame:
    out = df
    if countries:
        out = out[out["country"].isin(countries)]
    if gender and gender != "All":
        out = out[out["gender"] == gender]
    if age and age != "All":
        out = out[out["age_group"] == age]
    if urban and urban != "All":
        out = out[out["urban_rural"] == urban]
    if edu and edu != "All":
        out = out[out["education"] == edu]
    if income and income != "All":
        out = out[out["income_group"] == income]
    return out


def display_label(s: str, n: int | None = None) -> str:
    """Full answer wording for charts/legends — never truncate for the client."""
    # `n` kept for call-site compatibility; intentionally unused.
    _ = n
    return str(s).strip()


# Back-compat alias (no truncation)
short_label = display_label


INCOME_CLASS_NOTE = """
**How income groups are classified**

Original country income categories (S9) are grouped into Low / Medium / High for comparison:

| Country | Low | Medium | High |
|---|---|---|---|
| Afghanistan | < 30,000 Afn | 30,000–60,000 Afn | > 60,000 Afn |
| DRC (Congo) | < $150 | $150–$400 | > $400 |
| Ethiopia | < $100 or $100–$199 | $200–$749 | $750+ |
| Iran | ≤ 15m Tomans | 15–40m Tomans | > 40m Tomans |
| Kenya | ≤ 20,000 Ksh | 20,001–80,000 Ksh | > 80,000 Ksh |
| Laos | ≤ 3m LAK | 3–7m LAK | > 7m LAK |
| Nigeria | < 100,000 NGN | 100,000–350,000 NGN | > 350,000 NGN |
| Pakistan | ≤ 20,000 PKR | 20,001–50,000 PKR | > 50,000 PKR |
| Sri Lanka | ≤ 50,000 LKR | 50,001–150,000 LKR | > 150,000 LKR |
| Zimbabwe | up to $100 | $101–$500 | $501+ |

DK / refuse / missing answers are shown as **Not stated** and excluded from the Low–Medium–High slicer options.
"""


def country_pct_table(df: pd.DataFrame, col: str, order: list[str] | None) -> pd.DataFrame:
    rows = []
    # Resolve once against the full filtered sample so country charts share one sequence
    cats_all = resolve_order(df[col].tolist(), order) if order else None
    for ctry, sub in df.groupby("country", sort=True):
        vc = sub[col].astype(str).value_counts(dropna=False)
        total = vc.sum()
        if total == 0:
            continue
        cats = cats_all if cats_all else list(vc.index)
        for cat in list(cats) + [x for x in vc.index if x not in cats]:
            n = int(vc.get(cat, 0))
            if n == 0 and order and cat not in vc.index:
                # Keep QRE slots that appear elsewhere in the sample (0% for this country)
                if cats_all is None or cat not in cats_all:
                    continue
            rows.append(
                {
                    "Country": ctry,
                    "Answer": display_label(cat),
                    "Answer_full": cat,
                    "N": n,
                    "Percent": round(n / total * 100, 1) if total else 0.0,
                }
            )
    return pd.DataFrame(rows)


def positive_share(df: pd.DataFrame, col: str, positive: list[str] | None) -> pd.DataFrame:
    if not positive:
        return pd.DataFrame()
    rows = []
    for ctry, sub in df.groupby("country", sort=True):
        s = sub[col].astype(str)
        # soften match for truncated labels
        mask = s.isin(positive)
        for p in positive:
            mask = mask | s.str.startswith(p[:40])
        pct = mask.mean() * 100 if len(sub) else 0
        rows.append({"Country": ctry, "Percent": round(pct, 1), "N": len(sub)})
    return pd.DataFrame(rows)


def chart_layout(
    fig,
    title: str = "",
    legend_below: bool = False,
    legend_items: int = 0,
    longest_label: int = 0,
):
    """Tighten plot chrome. Legends are rendered in HTML (never truncated)."""
    _ = legend_items, longest_label, legend_below
    top = 28 if title else 16
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(color=COLORS["ink"], size=12, family="Source Sans 3, Segoe UI, sans-serif"),
        margin=dict(l=48, r=28, t=top, b=48),
        showlegend=False,
        hoverlabel=dict(bgcolor="white", font_size=12),
        bargap=0.28,
        uniformtext_minsize=8,
        uniformtext_mode=False,
    )
    fig.update_xaxes(
        gridcolor="rgba(0,0,0,0)",
        zeroline=False,
        tickangle=0,
        linecolor=COLORS["grid"],
        tickfont=dict(size=11),
        automargin=True,
    )
    fig.update_yaxes(
        gridcolor="#EEE8DE",
        zeroline=False,
        linecolor=COLORS["grid"],
        ticksuffix="%",
        tickfont=dict(size=11),
        automargin=True,
    )
    return fig


def show_plotly(fig, *, html_legend: bool = False, legend_pairs=None):
    """Render chart; optional HTML legend with full labels (no Plotly clip)."""
    pairs = legend_pairs
    if html_legend and pairs is None:
        pairs = legend_pairs_from_fig(fig)
    fig.update_layout(showlegend=False)
    st.markdown('<div class="cis-chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)
    if pairs:
        render_html_legend(pairs)


def after_visual():
    """Single 1px line between chart blocks."""
    st.markdown('<div class="cis-sep" role="separator"></div>', unsafe_allow_html=True)


def add_average_line(fig, avg: float):
    """Dotted grey reference line — label shown outside the plot."""
    fig.add_hline(
        y=avg,
        line_dash="dot",
        line_color="#8E8A82",
        line_width=1.6,
        opacity=1.0,
    )
    return fig


def show_table(df: pd.DataFrame):
    """HTML table — headers and values both left-aligned."""
    if df is None or df.empty:
        return
    view = df.copy()
    # Avoid index column
    if view.index.name is not None or not isinstance(view.index, pd.RangeIndex):
        view = view.reset_index(drop=True)
    cols = list(view.columns)
    thead = "".join(f"<th>{c}</th>" for c in cols)
    rows_html = []
    for _, row in view.iterrows():
        tds = "".join(f"<td>{'' if pd.isna(v) else v}</td>" for v in row.tolist())
        rows_html.append(f"<tr>{tds}</tr>")
    html = f"""
    <div class="cis-table-wrap">
      <table class="cis-table">
        <thead><tr>{thead}</tr></thead>
        <tbody>{''.join(rows_html)}</tbody>
      </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def main():
    if not _check_auth():
        return

    try:
        mtime = DATA_PATH.stat().st_mtime if DATA_PATH.exists() else 0.0
        df_all = load_data(mtime)
    except FileNotFoundError as e:
        st.error(str(e))
        return

    # ----- Sidebar -----
    with st.sidebar:
        st.markdown(
            '<div class="side-brand">Country Image Study 2026</div>'
            '<div class="side-brand-sub">CIS · 10 countries</div>'
            '<hr class="side-rule"/>',
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Section",
            ["Demographic profiles", "Survey findings"],
            index=0,
            key="app_section",
        )
        st.markdown('<hr class="side-rule"/>', unsafe_allow_html=True)

        all_countries = ordered_present(df_all["country"], COUNTRY_ORDER)
        if "sel_countries" not in st.session_state:
            st.session_state.sel_countries = all_countries.copy()

        sa, ua = st.columns(2)
        sa.button(
            "Select all",
            use_container_width=True,
            key="btn_sel_all_cty",
            on_click=lambda: st.session_state.update(sel_countries=all_countries.copy()),
        )
        ua.button(
            "Unselect all",
            use_container_width=True,
            key="btn_unsel_all_cty",
            on_click=lambda: st.session_state.update(sel_countries=[]),
        )
        countries = st.multiselect(
            "Countries",
            options=all_countries,
            key="sel_countries",
        )

        gender = age = urban = edu = income = "All"
        q = None
        view = "Country comparison (summary %)"

        if page == "Demographic profiles":
            st.caption("Country selection applies to all demographic tabs.")
        else:
            st.markdown("**Filters**")
            st.caption("Narrow the sample, then choose a question.")
            gender = st.selectbox(
                "Gender",
                ["All"] + ordered_present(df_all["gender"], GENDER_ORDER),
                key="flt_gender",
            )
            age = st.selectbox(
                "Age group",
                ["All"] + ordered_present(df_all["age_group"], AGE_ORDER),
                key="flt_age",
            )
            urban = st.selectbox(
                "Urban / rural",
                ["All"] + ordered_present(df_all["urban_rural"], URBAN_ORDER),
                key="flt_urban",
            )
            edu = st.selectbox(
                "Education (quota)",
                ["All"] + ordered_present(df_all["education"], EDU_ORDER),
                key="flt_edu",
            )
            income_opts = ["All"] + [
                x for x in INCOME_ORDER if x != "Not stated"
            ]
            if "income_group" in df_all.columns:
                income = st.selectbox("Income group", income_opts, key="flt_income")
                with st.expander("How income groups are classified"):
                    st.markdown(INCOME_CLASS_NOTE)
            else:
                income = "All"

            st.markdown('<hr class="side-rule"/>', unsafe_allow_html=True)
            sec = st.selectbox("Questionnaire section", sections())
            q_opts = [q for q in QUESTIONS if q["section"] == sec]
            q_label = st.selectbox("Question", [q["label"] for q in q_opts])
            q = next(q for q in q_opts if q["label"] == q_label)
            view = st.radio(
                "Chart view",
                ["Country comparison (summary %)", "Full answer mix by country"],
                index=0,
            )

    dff = apply_filters(df_all, countries, gender, age, urban, edu, income)

    st.markdown(
        '<div class="cis-title">A Global Survey on Impression and Understanding of China</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cis-sub">Country comparison of selected findings · 10 countries · 2026</div>',
        unsafe_allow_html=True,
    )

    if len(dff) == 0:
        st.warning("No respondents match these filters. Try widening the selection.")
        return

    # Metric cards only on Survey findings — demographics already shows N in the table
    if page == "Demographic profiles":
        render_demographic_profiles(dff)
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Respondents in view", f"{len(dff):,}")
    c2.metric("Countries in view", f"{dff['country'].nunique()}")
    n_lang = (
        int(dff["language"].nunique())
        if "language" in dff.columns
        else (int(dff["s1"].nunique()) if "s1" in dff.columns else 0)
    )
    c3.metric("Languages in view", f"{n_lang}")

    st.markdown(
        f'<div class="cis-qbox"><b>{q["label"]}</b><span>{q["text"]}</span></div>',
        unsafe_allow_html=True,
    )

    filter_bits = []
    if gender != "All":
        filter_bits.append(f"Gender: {gender}")
    if age != "All":
        filter_bits.append(f"Age: {age}")
    if urban != "All":
        filter_bits.append(f"Area: {urban}")
    if edu != "All":
        filter_bits.append(f"Education: {edu}")
    if income != "All":
        filter_bits.append(f"Income: {income}")
    if filter_bits:
        st.markdown(
            f'<div class="cis-note">Showing: {" · ".join(filter_bits)}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="cis-note">Showing all demographic groups in the selected countries.</div>',
            unsafe_allow_html=True,
        )

    col = q["col"]
    order = q.get("order")
    positive = q.get("positive")
    highlight = q.get("highlight")

    # ----- Main charts -----
    if view.startswith("Country comparison") and (positive or highlight):
        if highlight:
            rows = []
            for ctry, sub in dff.groupby("country", sort=True):
                s = sub[col].astype(str)
                pct = (s == highlight).mean() * 100
                # also startswith for long labels
                if pct == 0:
                    pct = s.str.startswith(str(highlight)[:50]).mean() * 100
                rows.append({"Country": ctry, "Percent": round(pct, 1), "N": len(sub)})
            pdf = pd.DataFrame(rows)
            metric_name = display_label(highlight)
            st.caption(f"Share selecting: {highlight}")
        else:
            pdf = positive_share(dff, col, positive)
            metric_name = " / ".join(display_label(p) for p in positive[:3])
            st.caption("Summary share (selected favourable / affirmative answers).")

        avg = float(pdf["Percent"].mean()) if len(pdf) else 0.0
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=pdf["Country"],
                y=pdf["Percent"],
                marker_color=COLORS["teal"],
                marker_line_width=0,
                text=[f"{v:.1f}" for v in pdf["Percent"]],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
                name="Country",
                showlegend=False,
            )
        )
        add_average_line(fig, avg)
        ymax = min(100, max(pdf["Percent"].max() + 14, avg + 14, 35))
        fig.update_yaxes(title_text="", range=[0, ymax])
        fig.update_xaxes(title_text="")
        chart_layout(fig)
        st.markdown(
            f'<div class="cis-avg">Dotted grey line = average across countries in view '
            f"({avg:.1f}%)</div>",
            unsafe_allow_html=True,
        )
        show_plotly(fig, html_legend=False)

        show = pdf.sort_values("Percent", ascending=False).reset_index(drop=True)
        show = show.rename(columns={"Percent": f"% — {metric_name}"})
        show_table(show)
        after_visual()

    else:
        # Full distribution — all answers, QRE order, full labels
        tab = country_pct_table(dff, col, order)
        if tab.empty:
            st.info("No data for this question under the current filters.")
            return

        resolved = resolve_order(dff[col].tolist(), order) if order else None
        cats: list[str] | None = None
        if resolved:
            cats = [display_label(x) for x in resolved]
            tab["Answer"] = tab["Answer_full"].map(display_label)
            tab["Answer"] = pd.Categorical(tab["Answer"], categories=cats, ordered=True)
            tab = tab.sort_values(["Country", "Answer"])
        else:
            # Show every answer present (no top-N hide)
            cats = (
                dff[col]
                .astype(str)
                .value_counts()
                .index.map(display_label)
                .tolist()
            )
            tab["Answer"] = tab["Answer_full"].map(display_label)
            tab["Answer"] = pd.Categorical(tab["Answer"], categories=cats, ordered=True)
            tab = tab.sort_values(["Country", "Answer"])

        fig = px.bar(
            tab,
            x="Country",
            y="Percent",
            color="Answer",
            barmode="group",
            color_discrete_sequence=COLORS["countries"],
            category_orders={"Answer": cats} if cats else None,
        )
        avg_note = ""
        if positive:
            key = display_label(positive[0])
            sub = tab[tab["Answer"] == key]
            if len(sub):
                avg = float(sub["Percent"].mean())
                add_average_line(fig, avg)
                avg_note = (
                    f'<div class="cis-avg">Dotted grey line = average for “{key}” '
                    f"across countries ({avg:.1f}%)</div>"
                )
        fig.update_yaxes(title_text="", range=[0, 100])
        fig.update_xaxes(title_text="")
        longest = max((len(str(c)) for c in (cats or [])), default=0)
        chart_layout(
            fig,
            legend_below=True,
            legend_items=len(cats or []),
            longest_label=longest,
        )
        if avg_note:
            st.markdown(avg_note, unsafe_allow_html=True)
        show_plotly(fig, html_legend=True)

        pivot = tab.pivot_table(
            index="Country", columns="Answer", values="Percent", aggfunc="first"
        ).reset_index()
        if cats:
            cols = ["Country"] + [c for c in cats if c in pivot.columns]
            pivot = pivot[[c for c in cols if c in pivot.columns]]
        show_table(pivot.round(1))
        after_visual()

    # ----- Optional demographic slice on same question -----
    st.markdown("#### Breakdown within the filtered sample")
    demo_dim = st.selectbox(
        "Split by",
        [
            "None",
            "Gender",
            "Age group",
            "Urban / rural",
            "Education (quota)",
            "Income group",
            "City (s5)",
        ],
        index=0,
    )
    dim_map = {
        "Gender": "gender",
        "Age group": "age_group",
        "Urban / rural": "urban_rural",
        "Education (quota)": "education",
        "Income group": "income_group",
        "City (s5)": "city",
    }
    if demo_dim != "None":
        dcol = dim_map[demo_dim]
        if dcol not in dff.columns:
            st.warning(
                f"“{demo_dim}” is not available in the loaded data. "
                "Rebuild with prepare_parquet.py and refresh."
            )
            return

        # Fixed QRE option order for demogs — show every slice (no N threshold / Other fold)
        demo_qre_order = {
            "Gender": GENDER_ORDER,
            "Age group": AGE_ORDER,
            "Urban / rural": URBAN_ORDER,
            "Education (quota)": EDU_ORDER,
            "Income group": INCOME_ORDER,
        }.get(demo_dim)

        if positive or highlight:
            hit_rows = []
            for (ctry, demo), sub in dff.groupby(["country", dcol], sort=True, dropna=False):
                s = sub[col].astype(str)
                if highlight:
                    hits = int((s == highlight).sum())
                    if hits == 0:
                        hits = int(s.str.startswith(str(highlight)[:50]).sum())
                else:
                    mask = s.isin(positive)
                    for p in positive:
                        mask = mask | s.str.startswith(p[:40])
                    hits = int(mask.sum())
                hit_rows.append(
                    {"Country": ctry, "_demo": demo, "Hits": hits, "N": len(sub)}
                )
            hdf = pd.DataFrame(hit_rows)
            if hdf.empty or hdf["Hits"].sum() == 0:
                st.info("No summarised answers in the current filter for this split.")
            else:
                if demo_qre_order:
                    demo_seq = ordered_present(hdf["_demo"], demo_qre_order)
                else:
                    # Cities: largest first, but keep every city
                    demo_seq = (
                        hdf.groupby("_demo", sort=False)["N"]
                        .sum()
                        .sort_values(ascending=False)
                        .index.astype(str)
                        .tolist()
                    )

                rows = []
                for ctry, g in hdf.groupby("Country", sort=True):
                    ctry_hits = int(g["Hits"].sum())
                    if ctry_hits == 0:
                        continue
                    by_demo = {str(r["_demo"]): r for _, r in g.iterrows()}
                    for demo_key in demo_seq:
                        if demo_key not in by_demo:
                            continue
                        r = by_demo[demo_key]
                        demo_lab = display_label(str(r["_demo"]).replace("_", " "))
                        if demo_dim == "City (s5)" and dff["country"].nunique() > 1:
                            demo_lab = f"{ctry}: {demo_lab}"
                        rows.append(
                            {
                                "Country": ctry,
                                demo_dim: demo_lab,
                                "Percent": round(r["Hits"] / ctry_hits * 100, 1),
                                "N": int(r["N"]),
                            }
                        )
                bdf = pd.DataFrame(rows)
                if bdf.empty:
                    st.info("No cases to show for this demographic split.")
                else:
                    if demo_qre_order:
                        legend_keys = [
                            display_label(x.replace("_", " ")) for x in demo_seq
                        ]
                        present_labs = set(bdf[demo_dim].astype(str))
                        legend_order = [x for x in legend_keys if x in present_labs]
                        legend_order += [
                            x
                            for x in bdf[demo_dim].astype(str).unique()
                            if x not in legend_order
                        ]
                    else:
                        legend_order = list(
                            dict.fromkeys(bdf[demo_dim].astype(str).tolist())
                        )

                    st.caption(
                        "Each bar = share of that country’s summarised answers in this slice. "
                        "Bars for a country total 100%. "
                        "All groups shown · questionnaire sequence."
                    )
                    fig2 = px.bar(
                        bdf,
                        x="Country" if demo_dim != "City (s5)" else demo_dim,
                        y="Percent",
                        color=demo_dim if demo_dim != "City (s5)" else "Country",
                        barmode="group",
                        color_discrete_sequence=COLORS["countries"],
                        category_orders=(
                            {demo_dim: legend_order}
                            if demo_dim != "City (s5)"
                            else None
                        ),
                    )
                    fig2.update_yaxes(range=[0, 100])
                    if demo_dim == "City (s5)":
                        fig2.update_xaxes(tickangle=-35, automargin=True)
                    avg2 = float(bdf["Percent"].mean())
                    add_average_line(fig2, avg2)
                    longest = max((len(str(x)) for x in legend_order), default=0)
                    chart_layout(
                        fig2,
                        legend_below=True,
                        legend_items=len(legend_order),
                        longest_label=longest,
                    )
                    st.markdown(
                        f'<div class="cis-avg">Dotted grey line = average across slices '
                        f"({avg2:.1f}%)</div>",
                        unsafe_allow_html=True,
                    )
                    show_plotly(fig2, html_legend=True)

                    tbl = bdf.copy()
                    if demo_qre_order and demo_dim in tbl.columns:
                        cat = pd.Categorical(
                            tbl[demo_dim],
                            categories=legend_order,
                            ordered=True,
                        )
                        tbl = tbl.assign(**{demo_dim: cat}).sort_values(
                            ["Country", demo_dim]
                        )
                    else:
                        tbl = tbl.sort_values(
                            ["Country", "Percent"], ascending=[True, False]
                        )
                    show_table(tbl)
                    after_visual()
        else:
            st.caption(
                "Pick a summary-style question to use the demographic split view, or use the full answer mix above."
            )

    # Overview strip for a few headline questions
    with st.expander("Quick look across a few headline questions (current filters)"):
        headlines = ["q3", "q11a", "q16", "q46"]
        cols = st.columns(len(headlines))
        for i, qid in enumerate(headlines):
            qq = next(x for x in QUESTIONS if x["id"] == qid)
            with cols[i]:
                if qq.get("positive"):
                    pdf = positive_share(dff, qq["col"], qq["positive"])
                elif qq.get("highlight"):
                    rows = []
                    for ctry, sub in dff.groupby("country"):
                        s = sub[qq["col"]].astype(str)
                        pct = (s == qq["highlight"]).mean() * 100
                        rows.append({"Country": ctry, "Percent": pct})
                    pdf = pd.DataFrame(rows)
                else:
                    pdf = pd.DataFrame()
                if len(pdf):
                    st.metric(qq["label"].split(". ", 1)[-1][:32], f"{pdf['Percent'].mean():.1f}%")
                    st.caption("Average across countries in view")


if __name__ == "__main__":
    main()
