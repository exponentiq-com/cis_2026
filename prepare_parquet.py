# -*- coding: utf-8 -*-
"""Build a lean parquet file for the CIS 2026 dashboard."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from questions import QUESTIONS

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
SRC = ROOT / "S22526_China_All_Countries_Final_WIDE successful+rejected 5-oct-2026 working (2).xlsx"
OUT = BASE / "data" / "cis2026.parquet"

COUNTRY_S9 = {
    "Laos": "s9_laos",
    "Kenya": "s9_kenya",
    "Ethiopia": "s9_ethiopia",
    "Afghanistan": "s9_afghanistan",
    "Congo": "s9_congo",
    "Iran": "s9_iran",
    "Nigeria": "s9_nigeria",
    "Pakistan": "s9_pakistan",
    "Sri_Lanka": "s9_srilanka",
    "Zimbabwe": "s9_zimbabwe",
}

DEMO_COLS = [
    "s0",
    "s1",
    "s3_label",
    "s4",
    "s5",
    "s5_1",
    "s7",
    "edu_quota",
    "region",
] + list(COUNTRY_S9.values())
Q_COLS = sorted({q["col"] for q in QUESTIONS})

# Same banding used in the QC / validation workbooks
INCOME_BAND: dict[str, str] = {}


def _ib(low, med, high, dk):
    for x in low:
        INCOME_BAND[x] = "Low"
    for x in med:
        INCOME_BAND[x] = "Medium"
    for x in high:
        INCOME_BAND[x] = "High"
    for x in dk:
        INCOME_BAND[x] = "DK/Refuse"


_ib(
    ["Less than 30000 Afn"],
    ["30000 Afn to 60000 Afn"],
    ["More than 60000 Afn"],
    ["Don’t know / refused to answer  (don’t read)", "Don't know / refused to answer  (don’t read)"],
)
_ib(
    ["Less than $150 : Low"],
    ["$150-$400 : Medium"],
    ["More than $400 : High"],
    ["Don’t know / refused to answer (don’t read)"],
)
_ib(
    ["less than $ 100", "$ 100 - $ 199"],
    ["$ 200-$ 299", "$ 300- $ 499", "$ 500 - $ 749"],
    ["$ 750 - $ 999", "$ 1000- $ 1999", "$ 2000- $ 3499", "$ 3500 - $ 5000", "More than $ 5000"],
    ["I don't know/Refuse (don’t read)"],
)
_ib(
    ["Below 10 million Tomans per month", "10–15 million Tomans"],
    ["15–25 million Tomans", "25–40 million Tomans"],
    ["More than 40 million Tomans per month"],
    ["Don’t know / refused to answer (don’t read)"],
)
_ib(
    ["10,000 Ksh or less / month", "10,001 – 20,000 Ksh / month"],
    ["20,001 – 50,000 Ksh / month", "50,001 – 80,000 Ksh / month"],
    ["80,001 – 100,000 Ksh / month", "100,001 – 150,000 Ksh / month", "Above 150,001 Ksh / month"],
    ["Don't Know / Refused (don’t read)"],
)
_ib(
    ["Less than 1,000,000 LAK", "1,000,000 to 3,000,000 LAK"],
    ["3,00,001 to 5,000,000 LAK", "5,000,001 to 7,000,000 LAK"],
    ["7,000,001 to 10,000,000 LAK", "More than 10,000,000 LAK"],
    [],
)
_ib(
    ["Below 100,000 NGN/month"],
    ["100,000 – 200,000 NGN/month", "200,001 – 350,000 NGN/month"],
    ["Above 350,000 NGN/month"],
    ["I don't know/Refuse (don’t read)"],
)
_ib(
    ["14,000 PKR or less", "14,001 PKR – 20,000 PKR"],
    ["20,001 PKR – 50,000 PKR"],
    ["More than 50,000 PKR"],
    ["Don’t know / refused to answer"],
)
_ib(
    ["Less than 30,000 LKR", "30,000-50,000 LKR"],
    ["50,001-75,000 LKR", "75,001-100,000 LKR", "100,001-150,000 LKR"],
    ["150,001-200,000 LKR", "More than200,000 LKR"],
    ["I don't know/Refuse (don’t read)"],
)
_ib(
    ["Low (up to $100)"],
    ["Medium ($101 - $500)"],
    ["High ($501 and above)"],
    ["Don’t know / refused to answer (don’t read)"],
)


def country_label(x: str) -> str:
    return {"Sri_Lanka": "Sri Lanka", "Congo": "DRC (Congo)"}.get(x, x)


def main():
    print("Reading", SRC.name)
    df = pd.read_excel(SRC)
    cols = [c for c in DEMO_COLS + Q_COLS if c in df.columns]
    out = df[cols].copy()
    for c in Q_COLS:
        if c in out.columns:
            out[c] = out[c].map(lambda x: "" if pd.isna(x) else str(x))

    income_raw = []
    for _, row in out.iterrows():
        ctry = row["s0"]
        s9 = COUNTRY_S9.get(ctry)
        income_raw.append(row[s9] if s9 and s9 in out.columns else pd.NA)
    out["income_raw"] = income_raw
    out["income_group"] = out["income_raw"].map(
        lambda x: INCOME_BAND.get(x, "Other") if pd.notna(x) else "Not stated"
    )
    # Keep Low/Medium/High as main slicer options; DK/Other stay in data
    out["income_group"] = out["income_group"].replace(
        {"DK/Refuse": "Not stated", "Other": "Not stated"}
    )

    out["country"] = out["s0"].map(country_label)
    out["gender"] = out["s4"].astype(str)
    out["age_group"] = out["s3_label"].astype(str)
    out["urban_rural"] = out["s5_1"].astype(str)
    out["education"] = out["edu_quota"].astype(str)
    out["city"] = out["s5"].astype(str)
    out["language"] = out["s1"].astype(str)
    out["occupation"] = out["s7"].astype(str) if "s7" in out.columns else "Not stated"
    _nonworking = {
        "Housewife",
        "Student",
        "Unemployed/ laid off/ retired",
    }
    out["work_status"] = out["occupation"].map(
        lambda x: "Non-working" if str(x) in _nonworking else "Working"
    )
    # Prefer survey region; fall back to city/area (s5)
    out["place"] = out["region"].where(out["region"].notna(), out["s5"]).astype(str)
    out["place"] = out["place"].replace({"nan": "Not stated", "": "Not stated"})

    keep = [
        "country",
        "gender",
        "age_group",
        "urban_rural",
        "education",
        "income_group",
        "city",
        "place",
        "language",
        "occupation",
        "work_status",
        "s0",
        "s1",
    ] + Q_COLS
    keep = [c for c in keep if c in out.columns]
    out = out[keep]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print("Saved", OUT, "rows=", len(out), "cols=", out.shape[1])
    print(out["income_group"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    main()
