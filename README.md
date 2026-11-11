# IB Exam Studio (Skompu)

Streamlit app for generating IB Mathematics AA HL practice papers and mark schemes.

## Local setup

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Optional: create `.streamlit/secrets.toml` with `GEMINI_API_KEY` (and payment keys if used). Do not commit secrets.

## Tests

```powershell
pytest -q
```

Tests must not import `app.py`. CI runs the same suite on push and pull requests to `main`.
