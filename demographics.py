# -*- coding: utf-8 -*-
"""Simple client-facing demographic profile summary for CIS 2026."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

NAVY = "#1B3A5F"
GOLD = "#C4A035"
TEAL = "#2F6F6A"
RURAL = "#A8B8C8"
INK = "#1F2A2E"

COUNTRY_ORDER = [
    "Afghanistan",
    "DRC (Congo)",
    "Ethiopia",
    "Iran",
    "Kenya",
    "Laos",
    "Nigeria",
    "Pakistan",
    "Sri Lanka",
    "Zimbabwe",
]
DISPLAY_COUNTRY = {"DRC (Congo)": "Congo"}

INACTIVE = {"Housewife", "Student", "Unemployed/ laid off/ retired"}
LANG_MIN = 100  # language quota floor

AGE_ORDER = [
    "18-29 years old",
    "30-39 years old",
    "40-49 years old",
    "50-60 years old",
    "61-70 years old",
]
AGE_SHORT = {
    "18-29 years old": "18-29",
    "30-39 years old": "30-39",
    "40-49 years old": "40-49",
    "50-60 years old": "50-60",
    "61-70 years old": "61-70",
}
AGE_COLORS = {
    "18-29": "#1B3A5F",
    "30-39": "#3D6BA5",
    "40-49": "#2F6F6A",
    "50-60": "#C4A035",
    "61-70": "#8B4513",
}

CROSS_VARS = {
    "Gender": ("gender", ["Male", "Female"]),
    "Age group": ("age_group", AGE_ORDER),
    "Urban / rural": ("urban_rural", ["Urban", "Rural"]),
    "Education": ("education", ["Bachelor and above", "Below Bachelor"]),
    "Work status": ("work_status", ["Working", "Non-working"]),
    "Income group": ("income_group", ["Low", "Medium", "High", "Not stated"]),
}


def _disp(ctry: str) -> str:
    return DISPLAY_COUNTRY.get(ctry, ctry)


def _ordered_countries(df: pd.DataFrame) -> list[str]:
    present = set(df["country"].dropna().unique())
    return [c for c in COUNTRY_ORDER if c in present] + sorted(
        c for c in present if c not in COUNTRY_ORDER
    )


def build_profile_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ctry in _ordered_countries(df):
        sub = df[df["country"] == ctry]
        n = len(sub)
        if n == 0:
            continue
        male = (sub["gender"].astype(str) == "Male").mean() * 100
        female = (sub["gender"].astype(str) == "Female").mean() * 100
        urban = (sub["urban_rural"].astype(str) == "Urban").mean() * 100
        bach = (sub["education"].astype(str) == "Bachelor and above").mean() * 100
        if "work_status" in sub.columns:
            inactive = (sub["work_status"].astype(str) == "Non-working").mean() * 100
        elif "occupation" in sub.columns:
            inactive = sub["occupation"].astype(str).isin(INACTIVE).mean() * 100
        else:
            inactive = 0.0
        cities_n = int(sub["city"].nunique()) if "city" in sub.columns else 0
        rows.append(
            {
                "Country": _disp(ctry),
                "N": n,
                "Male_%": round(male, 1),
                "Female_%": round(female, 1),
                "Urban_%": round(urban, 1),
                "Bachelor+_%": round(bach, 1),
                "Inactive_%": round(inactive, 1),
                "Cities_N": cities_n,
            }
        )
    return pd.DataFrame(rows)


def _show_table(df: pd.DataFrame):
    if df is None or df.empty:
        return
    view = df.copy().reset_index(drop=True)
    cols = list(view.columns)
    thead = "".join(f"<th>{c}</th>" for c in cols)
    rows_html = []
    for _, row in view.iterrows():
        tds = "".join(f"<td>{'' if pd.isna(v) else v}</td>" for v in row.tolist())
        rows_html.append(f"<tr>{tds}</tr>")
    st.markdown(
        f"""
        <div class="cis-table-wrap demo-table">
          <table class="cis-table demo-cis-table">
            <thead><tr>{thead}</tr></thead>
            <tbody>{''.join(rows_html)}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _chart_frame(fig, title: str, *, has_legend: bool = True, left_margin: int = 120):
    existing_h = fig.layout.height
    bottom = 110 if has_legend else 56
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=14, color=NAVY),
            x=0.5,
            xanchor="center",
            y=0.98,
            yanchor="top",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(color=INK, size=12, family="Source Sans 3, Segoe UI, sans-serif"),
        margin=dict(l=left_margin, r=48, t=56, b=bottom, pad=4),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            x=0.5,
            xanchor="center",
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(size=11, color=INK),
            title=dict(text=""),
            itemsizing="constant",
            itemwidth=40,
            tracegroupgap=16,
            entrywidthmode="pixels",
            entrywidth=88,
        ),
        legend_title_text="",
        bargap=0.22,
        height=existing_h if existing_h else (420 if has_legend else 360),
        uniformtext_minsize=9,
        uniformtext_mode="hide",
    )
    # Keep axis titles off the top so they never collide with the chart title
    fig.update_xaxes(title_text="", title=None)
    fig.update_yaxes(title_text="", title=None, automargin=True, ticklabelposition="outside")
    st.markdown('<div class="cis-chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)


def _stacked_100(
    df: pd.DataFrame,
    col: str,
    order: list[str],
    colors: dict[str, str],
    title: str,
    label_map: dict[str, str] | None = None,
    threshold: float | None = None,
    threshold_label: str = "",
    color_col: str = "Group",
):
    """One horizontal bar per country; categories share the bar."""
    if col not in df.columns:
        st.caption(f"{title}: not available in data.")
        return
    label_map = label_map or {}
    order_cty = _ordered_countries(df)
    rows = []
    for ctry in order_cty:
        sub = df[df["country"] == ctry]
        if len(sub) == 0:
            continue
        s = sub[col].astype(str)
        for cat in order:
            rows.append(
                {
                    "Country": _disp(ctry),
                    color_col: label_map.get(cat, cat),
                    "N": int((s == cat).sum()),
                }
            )
    plot = pd.DataFrame(rows)
    if plot.empty:
        return
    cat_order = [label_map.get(c, c) for c in order]
    cmap = {}
    for cat in order:
        lab = label_map.get(cat, cat)
        cmap[lab] = colors.get(lab, colors.get(cat, TEAL))

    # Pre-compute % within country so each bar totals 100
    plot["Percent"] = plot.groupby("Country")["N"].transform(
        lambda s: (s / s.sum() * 100).round(1) if s.sum() else 0
    )
    fig = px.bar(
        plot,
        x="Percent",
        y="Country",
        color=color_col,
        orientation="h",
        barmode="stack",
        text="Percent",
        color_discrete_map=cmap,
        category_orders={
            "Country": [_disp(c) for c in reversed(order_cty)],
            color_col: cat_order,
        },
        labels={color_col: "", "Percent": "", "Country": ""},
    )
    fig.update_traces(
        texttemplate="%{x:.0f}%",
        textposition="inside",
        textfont_size=11,
        cliponaxis=True,
        hovertemplate="%{y} · %{fullData.name}: %{x:.1f}%<extra></extra>",
    )
    fig.update_xaxes(
        range=[0, 100],
        ticksuffix="%",
        dtick=20,
        side="bottom",
        gridcolor="#EEE8DE",
        title_text="",
        automargin=True,
    )
    fig.update_yaxes(title_text="", automargin=True)
    if threshold is not None:
        fig.add_vline(x=threshold, line_dash="dot", line_color=GOLD, line_width=1.8)
    _chart_frame(fig, title, has_legend=True)
    if threshold is not None:
        st.caption(f"Dotted line = {threshold_label or 'reference'} ({threshold:g}%).")


def _simple_pct_bar(
    df: pd.DataFrame,
    col: str,
    value: str,
    title: str,
    color: str = TEAL,
    threshold: float | None = None,
    threshold_label: str = "",
):
    """Single-series % bar by country (not stacked)."""
    if col not in df.columns:
        st.caption(f"{title}: not available in data.")
        return
    order_cty = _ordered_countries(df)
    rows = []
    for ctry in order_cty:
        sub = df[df["country"] == ctry]
        if len(sub) == 0:
            continue
        pct = round((sub[col].astype(str) == value).mean() * 100, 1)
        rows.append({"Country": _disp(ctry), "Percent": pct})
    plot = pd.DataFrame(rows)
    if plot.empty:
        return
    fig = px.bar(
        plot,
        x="Percent",
        y="Country",
        orientation="h",
        text="Percent",
        color_discrete_sequence=[color],
        category_orders={"Country": [_disp(c) for c in reversed(order_cty)]},
        labels={"Percent": "", "Country": ""},
    )
    fig.update_traces(texttemplate="%{x}%", textposition="outside", cliponaxis=False)
    xmax = max(plot["Percent"].max() + 10, (threshold or 0) + 12, 40)
    fig.update_xaxes(
        range=[0, xmax],
        ticksuffix="%",
        title_text="",
        gridcolor="#EEE8DE",
        side="bottom",
        automargin=True,
    )
    fig.update_yaxes(title_text="", automargin=True)
    if threshold is not None:
        fig.add_vline(x=threshold, line_dash="dot", line_color=GOLD, line_width=1.8)
    fig.update_layout(showlegend=False)
    _chart_frame(fig, title, has_legend=False)
    if threshold is not None:
        st.caption(f"Dotted line = {threshold_label or 'reference'} ({threshold:g}%).")


def _language_counts(df: pd.DataFrame):
    lang_col = "language" if "language" in df.columns else None
    if not lang_col:
        st.caption("Languages: not available in data.")
        return
    rows = []
    for (ctry, lang), sub in df.groupby(["country", lang_col], sort=True):
        rows.append(
            {
                "Label": f"{_disp(ctry)} – {lang}",
                "Count": len(sub),
                "_cty": ctry,
                "Language": str(lang),
            }
        )
    plot = pd.DataFrame(rows).sort_values(["_cty", "Language"])
    if plot.empty:
        return
    fig = px.bar(
        plot,
        x="Count",
        y="Label",
        orientation="h",
        text="Count",
        color_discrete_sequence=[NAVY],
        category_orders={"Label": list(reversed(plot["Label"].tolist()))},
        labels={"Count": "", "Label": ""},
    )
    fig.update_traces(texttemplate="%{x}", textposition="outside", cliponaxis=False)
    fig.update_xaxes(title_text="", gridcolor="#EEE8DE", side="bottom", automargin=True)
    fig.update_yaxes(
        title_text="",
        automargin=True,
        tickfont=dict(size=11),
        ticklabeloverflow="allow",
        ticksuffix="  ",
    )
    fig.add_vline(x=LANG_MIN, line_dash="dot", line_color=GOLD, line_width=1.6)
    # Wide left margin so "Country – Language" labels are not clipped
    longest = int(plot["Label"].astype(str).str.len().max() or 20)
    left = max(160, min(280, 8 * longest + 24))
    fig.update_layout(showlegend=False, height=max(480, 30 * len(plot) + 120))
    _chart_frame(fig, "Completes by language", has_legend=False, left_margin=left)
    st.caption(f"Bars show interview counts. Dotted line = minimum of {LANG_MIN}.")


def render_charts(df: pd.DataFrame):
    st.markdown("#### Gender")
    _stacked_100(
        df,
        "gender",
        ["Male", "Female"],
        {"Male": NAVY, "Female": GOLD},
        "Gender",
    )

    st.markdown("#### Urban / rural")
    _stacked_100(
        df,
        "urban_rural",
        ["Urban", "Rural"],
        {"Urban": NAVY, "Rural": RURAL},
        "Urban / rural",
    )

    st.markdown("#### Age")
    _stacked_100(
        df,
        "age_group",
        AGE_ORDER,
        AGE_COLORS,
        "Age",
        label_map=AGE_SHORT,
    )

    st.markdown("#### Income")
    _stacked_100(
        df,
        "income_group",
        ["Low", "Medium", "High", "Not stated"],
        {
            "Low": "#6B7F5A",
            "Medium": NAVY,
            "High": GOLD,
            "Not stated": "#B0A99C",
        },
        "Income",
    )

    st.markdown("#### Education")
    _simple_pct_bar(
        df,
        "education",
        "Bachelor and above",
        "Bachelor and above",
        color=TEAL,
        threshold=50,
        threshold_label="Bachelor+ limit",
    )

    st.markdown("#### Inactive population")
    if "work_status" in df.columns:
        _simple_pct_bar(
            df,
            "work_status",
            "Non-working",
            "Inactive population",
            color=GOLD,
            threshold=15,
            threshold_label="Inactive limit",
        )
    else:
        st.caption("Inactive population: not available in data.")

    st.markdown("#### Languages")
    _language_counts(df)


def render_cross_tab(df: pd.DataFrame):
    available = {k: v for k, v in CROSS_VARS.items() if v[0] in df.columns}
    if len(available) < 2:
        st.info("Cross-tab needs at least two demographic variables.")
        return

    keys = list(available.keys())
    c1, c2, c3 = st.columns(3)
    with c1:
        row_var = st.selectbox("Rows", keys, key="xt_rows")
    with c2:
        col_var = st.selectbox(
            "Columns", [k for k in keys if k != row_var], key="xt_cols"
        )
    with c3:
        scope = st.selectbox(
            "Country",
            ["All countries"] + [_disp(c) for c in _ordered_countries(df)],
            key="xt_cty",
        )

    work = df
    if scope != "All countries":
        raw = next((k for k, v in DISPLAY_COUNTRY.items() if v == scope), scope)
        work = df[df["country"] == raw]
        if work.empty:
            work = df[df["country"].map(_disp) == scope]
    if work.empty:
        st.warning("No respondents for this selection.")
        return

    r_col, r_order = available[row_var]
    c_col, c_order = available[col_var]
    show = st.radio("Show", ["Row %", "Counts"], horizontal=True, key="xt_show")

    if show == "Row %":
        ct = (
            pd.crosstab(
                work[r_col].astype(str), work[c_col].astype(str), normalize="index"
            )
            * 100
        ).round(1)
    else:
        ct = pd.crosstab(work[r_col].astype(str), work[c_col].astype(str))

    ct = ct.reindex(index=[x for x in r_order if x in ct.index])
    ct = ct[[x for x in c_order if x in ct.columns]]
    st.caption(f"{row_var} × {col_var} · {scope}")
    out = ct.reset_index().rename(columns={ct.index.name or "index": row_var})
    if row_var == "Age group" and row_var in out.columns:
        out[row_var] = out[row_var].map(lambda x: AGE_SHORT.get(x, x))
    for col in list(out.columns):
        if col in AGE_SHORT:
            out = out.rename(columns={col: AGE_SHORT[col]})
    _show_table(out)


def render_demographic_profiles(df: pd.DataFrame, filter_note: str = ""):
    st.markdown("### Demographic profiles")
    st.caption("Updated view · simple bars for Bachelor+ / Inactive / Languages")
    if filter_note:
        st.markdown(f'<div class="cis-note">{filter_note}</div>', unsafe_allow_html=True)

    profile = build_profile_table(df)
    if profile.empty:
        st.warning("No data to display.")
        return

    tab1, tab2 = st.tabs(["Country profile", "Cross-tab"])

    with tab1:
        st.caption(
            "Inactive = housewives + students + unemployed/retired."
        )
        display = profile.copy()
        display["N"] = display["N"].map(lambda x: f"{x:,}")
        _show_table(display)

        st.markdown("#### Demographic charts")
        render_charts(df)

    with tab2:
        st.caption("Two demographics × optional country.")
        render_cross_tab(df)
