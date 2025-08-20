# SwimForge – Secure Registration & Login

Now includes:
- **Create account** tab with password policy
- **bcrypt** password hashing
- Optional **encryption at rest** of user DB (`.data/users.enc`) using **Fernet** from `cryptography`.
- If no Fernet key is configured, the app stores a hashed-only JSON (`.data/users.json`) and shows a warning.

## Enable encryption at rest
Add a Fernet key to Streamlit **Secrets** (recommended):
```
[auth]
fernet_key = "<YOUR_FERNET_KEY>"
```
Generate a key (one-time) in Python:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```
Alternatively set env var `FERNET_KEY` with the same value.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
