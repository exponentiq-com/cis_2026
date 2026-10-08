---
title: CIS 2026 (10 Countries)
emoji: 📊
colorFrom: green
colorTo: gray
sdk: streamlit
sdk_version: 1.39.0
app_file: app.py
pinned: false
license: other
---

# CIS 2026 (10 Countries)

Client dashboard for the Global Survey on Impression and Understanding of China (2026).  
Country comparison of selected closed questions, with optional demographic filters.

## Confidentiality

This Space should be **private**. Do not make the Space or the data file public.

Set Space secrets (Settings → Secrets):

```
DASHBOARD_USER=your_client_username
DASHBOARD_PASS=a_long_random_password
```

Sign-in is required when `DASHBOARD_PASS` is set.

## Data file

Place the prepared sample here before deploying:

`data/cis2026.parquet`

Build it locally from the Excel working file:

```bash
pip install -r requirements.txt
python prepare_parquet.py
```

## Local preview

```bash
streamlit run app.py
```

If `DASHBOARD_PASS` is not set, the app opens in local preview mode.

## Notes for readers

- Percentages are unweighted within the filtered sample.
- Question wording follows the field questionnaire.
- The dashed line on charts is the average across countries currently in view.
