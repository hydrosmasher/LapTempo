# SwimForge – Banner/Logo Added; Strategy Removed
- Even pacing only (no strategy selector)
- Banner (`assets/banner.png`) at the top and logo (`assets/logo.png`) in the sidebar
- Secure registration/login with bcrypt + optional Fernet encryption at rest

## Run
```bash
pip install -r requirements.txt
mkdir -p assets   # put banner.png and logo.png here
streamlit run app.py
```
