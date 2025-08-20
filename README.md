# SwimForge – Secure Auth, Banner/Logo, Reset/Close Buttons

Features:
- **Secure registration/login** with bcrypt hashing and optional Fernet encryption at rest.
- **Banner/logo support**: place `assets/banner.png` and `assets/logo.png` in `./assets/`.
- **Pre-race planner**: Even pacing distribution only (strategy removed).
- **Post-race analyzer**: Paste splits (50/100), PB input, metrics & recommendations.
- **Reset App button** clears session and reruns.
- **Close App button** clears state and halts execution (stop Streamlit server manually with Ctrl+C).

## Run
```bash
pip install -r requirements.txt
mkdir -p assets
streamlit run app.py
```

## Enable encryption at rest
Generate a Fernet key once:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```
Add it to `.streamlit/secrets.toml`:
```toml
[auth]
fernet_key = "PASTE_KEY"
```
