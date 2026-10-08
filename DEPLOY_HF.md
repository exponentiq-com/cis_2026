# Hosting CIS 2026 on Hugging Face (private + sign-in)

## 1. Create a private Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Name: e.g. `cis-2026-10-countries`
3. SDK: **Streamlit**
4. Visibility: **Private** (required — survey data is confidential)
5. Create the Space

## 2. Upload the app

Upload these files into the Space (web UI or `huggingface-cli upload`):

- `app.py`
- `questions.py`
- `prepare_parquet.py` (optional on the Space)
- `requirements.txt`
- `README.md` (keep the YAML header at the top)
- `.streamlit/config.toml`
- `data/cis2026.parquet`  ← prepared sample only (not the full Excel)

Do **not** upload the full WIDE Excel workbook if you can avoid it.

## 3. Set sign-in secrets

Space → **Settings** → **Secrets**:

```toml
DASHBOARD_USER = "client_user"
DASHBOARD_PASS = "replace_with_a_long_password"
```

Restart the Space after saving secrets.

## 4. Share with the client

- Invite their HF account to the **private Space** (Settings → People), **or**
- Share the Space URL plus the username/password from secrets

Both layers matter: private Space + app password.

## 5. Local check before upload

```bash
cd cis2026_dashboard
pip install -r requirements.txt
python prepare_parquet.py
streamlit run app.py
```
