# SwimForge – Competitive Pacing with Secure Registration/Login
from __future__ import annotations
import os, math, json, time
from typing import List, Tuple, Dict
from datetime import date, datetime
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# ---- optional crypto for encrypting the user database at rest ----
FERNET_AVAILABLE = False
try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except Exception:
    pass

# ---- password hashing ----
try:
    import bcrypt
    HAS_BCRYPT = True
except Exception:
    HAS_BCRYPT = False

APP_TITLE = "SwimForge"
APP_TAGLINE = "Where Science Shapes Speed"
POWERED_BY = "Powered by HydroSmasher"

st.set_page_config(page_title=APP_TITLE, page_icon="🏊", layout="wide")

# ============================= Styling =============================
st.markdown("""
<style>
.block-container {padding-top: 0rem; padding-bottom: 3rem; max-width: 1200px;}
.hero {
  border-radius: 18px;
  padding: 28px 32px;
  margin: 18px 0 22px 0;
  background: radial-gradient(1200px 300px at 10% -10%, rgba(70,130,255,0.25) 0%, rgba(70,130,255,0) 60%),
              radial-gradient(1000px 250px at 95% -20%, rgba(0,200,255,0.20) 0%, rgba(0,200,255,0) 60%),
              linear-gradient(135deg, #0D1A35 0%, #0B1430 60%, #0A122C 100%);
  border: 1px solid rgba(120,150,255,0.12);
  text-align: center;
}
.hero h1 { margin: 0; font-size: 40px; line-height: 1.2; letter-spacing: 0.2px;}
.hero .sub { margin-top: 6px; opacity: 0.9; }
.hero .powered { margin-top: 4px; font-size: 12px; opacity: 0.65; }
.h1 {font-size: 28px; font-weight: 800; margin-top: 4px; display:flex; align-items:center; gap:8px;}
.sf-card { background: rgba(255,255,255,0.02); border: 1px solid rgba(120,150,255,0.12);
  border-radius: 16px; padding: 18px; margin-bottom: 16px;}
.stButton>button { border-radius: 12px; padding: 10px 16px; font-weight: 600;
  border: 1px solid rgba(120,150,255,0.25);}
header {visibility: hidden;}
.small {font-size: 12px; opacity:.7;}
</style>
""", unsafe_allow_html=True)

def hero():
    st.markdown(f"""
    <div class="hero">
      <h1>{APP_TITLE}</h1>
      <div class="sub">{APP_TAGLINE}</div>
      <div class="powered">{POWERED_BY}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================= Secure user DB =============================
USERS_PATH_PLAIN = os.path.join(".data", "users.json")
USERS_PATH_ENC = os.path.join(".data", "users.enc")

def _get_fernet():
    """Return a Fernet cipher if available and a key is configured in secrets or env."""
    if not FERNET_AVAILABLE:
        return None
    key = None
    # Preferred: st.secrets["auth"]["fernet_key"]
    try:
        if "auth" in st.secrets and "fernet_key" in st.secrets["auth"]:
            key = st.secrets["auth"]["fernet_key"]
    except Exception:
        pass
    # Fallback: env var
    if not key:
        key = os.getenv("FERNET_KEY", "")
    if not key:
        return None
    try:
        return Fernet(key.encode() if not key.startswith("gAAAA") else key)
    except Exception:
        return None

def _bcrypt_hash(pw: str) -> str:
    if not HAS_BCRYPT:
        raise RuntimeError("bcrypt is required for password hashing")
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()

def _bcrypt_check(pw: str, hashed: str) -> bool:
    if not HAS_BCRYPT:
        return False
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False

def _load_users() -> Dict[str, Dict]:
    """Load users from encrypted file if possible, otherwise from plain JSON. Returns dict keyed by username (lower)."""
    cipher = _get_fernet()
    # Encrypted preferred
    if cipher and os.path.exists(USERS_PATH_ENC):
        try:
            with open(USERS_PATH_ENC, "rb") as f:
                data = cipher.decrypt(f.read())
            return json.loads(data.decode())
        except Exception:
            st.warning("User database decryption failed. Admin: check your FERNET_KEY in secrets/env.", icon="⚠️")
            return {}
    # Plain fallback
    if os.path.exists(USERS_PATH_PLAIN):
        try:
            with open(USERS_PATH_PLAIN, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_users(users: Dict[str, Dict]):
    """Save users; encrypt at rest when key present. Only hashes are stored, never plaintext."""
    cipher = _get_fernet()
    os.makedirs(".data", exist_ok=True)
    payload = json.dumps(users, ensure_ascii=False).encode()
    if cipher:
        with open(USERS_PATH_ENC, "wb") as f:
            f.write(cipher.encrypt(payload))
        # Avoid leaving stale plain file
        if os.path.exists(USERS_PATH_PLAIN):
            try: os.remove(USERS_PATH_PLAIN)
            except Exception: pass
    else:
        # No key configured: store hashed users unencrypted (not ideal). Warn admins in UI.
        with open(USERS_PATH_PLAIN, "w", encoding="utf-8") as f:
            f.write(payload.decode())

def register_user(username: str, password: str) -> Tuple[bool, str]:
    """Create new user with bcrypt hash. Returns (ok, message)."""
    u = (username or "").strip().lower()
    if not u or " " in u or len(u) < 3:
        return False, "Username must be at least 3 characters and have no spaces."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password):
        return False, "Password must include letters and numbers."
    users = _load_users()
    if u in users:
        return False, "Username already exists."
    try:
        users[u] = {
            "pw_hash": _bcrypt_hash(password),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "role": "user"
        }
        _save_users(users)
        return True, "Account created. You can now sign in."
    except Exception as e:
        return False, f"Registration failed: {e}"

def authenticate(username: str, password: str) -> bool:
    u = (username or "").strip().lower()
    users = _load_users()
    if u not in users:
        return False
    return _bcrypt_check(password, users[u].get("pw_hash",""))

# ============================= App Logic (pacing/analyzer) =============================
def parse_time_to_seconds(s: str) -> float:
    s = str(s).strip()
    if not s: return math.nan
    if ":" in s:
        parts = [p.strip() for p in s.split(":")]
        if len(parts)==3:
            h,m,sec = parts; return int(h)*3600 + int(m)*60 + float(sec)
        if len(parts)==2:
            m,sec = parts; return int(m)*60 + float(sec)
    return float(s)

def format_seconds(t: float) -> str:
    if t is None or (isinstance(t,float) and (math.isnan(t) or math.isinf(t))): return ""
    t = float(t); m = int(t//60); s=t-60*m
    return f"{m}:{s:05.2f}" if m>0 else f"{s:.2f}s"

def coerce_splits_str_to_seconds_list(s: str):
    if not s: return []
    for d in [";", ",", "\n", "\t"]: s = s.replace(d, " ")
    return [parse_time_to_seconds(t) for t in s.split() if t.strip()]

def expand_100_splits_to_50(splits_100: List[float]) -> List[float]:
    out=[]; [out.extend([s/2.0, s/2.0]) for s in splits_100]; return out

def safe_altair_chart(df: pd.DataFrame, x: str, y: str, title: str):
    chart = alt.Chart(df).mark_line(point=True).encode(x=x, y=y, tooltip=[x,y]).properties(title=title).interactive()
    st.altair_chart(chart, use_container_width=True)

def pacing_plan(distance_m: int, target_time_s: float, strategy: str="Even", pb50_s: float|None=None):
    n = int(distance_m // 50)
    if n<=0: return []
    base = target_time_s / n
    if distance_m<=200: frac=0.05
    elif distance_m<=400: frac=0.035
    else: frac=0.025
    delta = max(0.10, frac*base)
    xs = np.arange(n, dtype=float)
    if strategy=="Negative":
        trend = np.linspace(base + delta, base - delta, n)
    elif strategy=="Descending":
        trend = base + (delta * (1.0 - (xs / (n - 1 if n>1 else 1.0))))
        trend = trend * (target_time_s / trend.sum())
    else:
        trend = np.full(n, base)
    if pb50_s and pb50_s>0:
        floor = 0.95*pb50_s if distance_m>=200 else 0.90*pb50_s
        trend = np.maximum(trend, floor)
    trend = trend * (target_time_s / trend.sum())
    return trend.tolist()

def analyze_post_race(splits_50: List[float], pb50_s: float|None):
    s = np.array(splits_50, dtype=float); n=len(s)
    total=float(np.sum(s)); mean=float(np.mean(s))
    stdev=float(np.std(s, ddof=1)) if n>1 else 0.0
    cv=(stdev/mean*100.0) if mean>0 else 0.0
    slope = float(np.polyfit(np.arange(n, dtype=float), s, 1)[0]) if n>=2 else 0.0
    fastest=float(np.min(s)) if n else math.nan
    slowest=float(np.max(s)) if n else math.nan
    delta_vs_mean = s-mean
    delta_vs_pb = s-(pb50_s if (pb50_s and pb50_s>0) else np.nan)
    pct_from_best = (s-fastest)/fastest*100.0 if fastest>0 else np.zeros(n)
    details = pd.DataFrame({
        "Lap (50m)": np.arange(1,n+1),
        "Split (s)": np.round(s,2),
        "Split (mm:ss)": [format_seconds(x) for x in s],
        "Δ vs mean (s)": np.round(delta_vs_mean,2),
        "Δ vs 50 PB (s)": np.round(delta_vs_pb,2),
        "% from fastest (%)": np.round(pct_from_best,2),
        "Cumulative (mm:ss)": [format_seconds(sum(s[:i+1])) for i in range(n)],
    })
    metrics = {
        "Total (mm:ss)": format_seconds(total),
        "Average per-50": format_seconds(mean),
        "Std dev (s)": round(stdev,2),
        "CV (%)": round(cv,2),
        "Slope (sec per 50)": round(slope,3),
        "Fastest 50": format_seconds(fastest),
        "Slowest 50": format_seconds(slowest),
        "Laps (50m)": n,
    }
    tips=[]
    if n>=2:
        if s[0] < mean*0.94: tips.append("Opening 50 was **too fast**. Aim for smoother settle.")
        elif s[0] > mean*1.05: tips.append("Opening 50 was **too conservative**. Consider a sharper start.")
    if n>=4 and s[-1] <= mean*0.98: tips.append("**Strong finish**—last 50 at/under average.")
    elif n>=4 and s[-1] >= mean*1.05: tips.append("**Fade at the end**. Build aerobic/threshold with race-pace 50s.")
    if cv >= 3.0: tips.append(f"Pacing variability (CV={cv:.1f}%) is high. Target **even splits**.")
    else: tips.append(f"Pacing variability (CV={cv:.1f}%) is solid.")
    if slope>0.10: tips.append("Splits trend **slower**; focus on technique under fatigue.")
    elif slope<-0.10: tips.append("Splits trend **faster**; nice negative split tendency.")
    if pb50_s and pb50_s>0:
        if np.any(s < 0.95*pb50_s): tips.append("Some 50s near raw 50 PB—beware **over‑speeding** early.")
        if np.any(s > 1.20*pb50_s): tips.append("Some 50s >120% of PB—improve **turns & underwater**.")
    if n>=3:
        idx = np.argsort(-s)[:3]; laps = ", ".join([f"{i+1}" for i in sorted(idx)])
        tips.append(f"Focus laps (slowest): **{laps}**.")
    return details, metrics, tips

# ============================= UI =============================
def login_or_register():
    hero()
    tab_login, tab_register = st.tabs(["Sign in", "Create account"])

    with tab_login:
        st.info("Sign in with your username and password.")
        with st.form("login_form", clear_on_submit=False):
            u = st.text_input("Username", value="", autocomplete="username")
            p = st.text_input("Password", value="", type="password", autocomplete="current-password")
            s = st.form_submit_button("Sign in")
        if s:
            if authenticate(u, p):
                st.session_state["authed"] = True
                st.session_state["username"] = u.strip()
                st.success("Logged in!"); st.rerun()
            else:
                st.error("Invalid username or password.")

        # Security status
        cipher = _get_fernet()
        st.caption(("🔐 Encrypted user DB enabled." if cipher else "🟡 User DB stored as hashed but unencrypted. "
                    "Admins: add `auth.fernet_key` in Streamlit **Secrets** to enable encryption at rest."))

    with tab_register:
        st.info("Create a new account. Passwords are hashed with bcrypt; optional encryption at rest via Fernet.")
        with st.form("register_form", clear_on_submit=True):
            u = st.text_input("New username", value="", autocomplete="username")
            p1 = st.text_input("New password", value="", type="password", help="Min 8 chars; must include letters and numbers.")
            p2 = st.text_input("Confirm password", value="", type="password")
            agree = st.checkbox("I understand that my credentials will be stored securely (hashed; optionally encrypted at rest).")
            s = st.form_submit_button("Create account")
        if s:
            if not agree:
                st.error("Please confirm the checkbox.")
            elif p1 != p2:
                st.error("Passwords do not match.")
            else:
                ok, msg = register_user(u, p1)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.balloons()

def logout_button():
    with st.sidebar:
        if st.button("Log out", use_container_width=True):
            st.session_state.clear(); st.rerun()

def main_page():
    # Title like screenshot
    st.markdown('<div class="h1">🛟 Race Split</div>', unsafe_allow_html=True)
    st.caption("Pre-race optimal splits and post-race analysis")

    # Race Setup
    st.markdown('<div class="sf-card">', unsafe_allow_html=True)
    st.markdown("### Race Setup")
    c1,c2,c3,c4 = st.columns([1,1,1,1])
    race_day = c1.date_input("Race day", value=date.today())
    stroke = c2.selectbox("Stroke", ["free","back","breast","fly","IM"], index=0)
    distance = c3.number_input("Distance (m)", min_value=50, max_value=1500, step=50, value=50)
    mode = c4.radio("Mode", ["Pre-race","Post-race"], horizontal=True, index=0)
    st.markdown('</div>', unsafe_allow_html=True)

    if mode=="Pre-race":
        st.markdown('<div class="sf-card">', unsafe_allow_html=True)
        st.markdown("### Pre-race inputs")
        c5,c6,c7 = st.columns([1,1,1])
        pb50 = c5.number_input("50m Personal Best (s)", min_value=0.0, step=0.01, value=24.00, format="%.2f")
        target_total = c6.number_input("Target time for event (s)", min_value=0.0, step=0.01, value=120.00, format="%.2f")
        pool_len = c7.selectbox("Pool length", [25,50], index=1)
        strat = st.radio("Strategy", ["Even","Negative","Descending"], horizontal=True, index=1)
        act = st.button("Compute optimal splits", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

        if act:
            splits = pacing_plan(int(distance), float(target_total), strategy=strat, pb50_s=float(pb50))
            if not splits:
                st.warning("Enter valid inputs.")
            else:
                df = pd.DataFrame({
                    "Lap (50m)": np.arange(1,len(splits)+1),
                    "Target Split (s)": np.round(splits,2),
                    "Target Split (mm:ss)": [format_seconds(x) for x in splits],
                    "Cumulative (mm:ss)": [format_seconds(sum(splits[:i+1])) for i in range(len(splits))],
                })
                st.success(f"Target average per-50: **{format_seconds(float(target_total)/(int(distance)/50))}**")
                st.dataframe(df, use_container_width=True, hide_index=True)
                safe_altair_chart(df, "Lap (50m)", "Target Split (s)", "Pacing Plan (per-50)")
                st.download_button("Download pacing plan (CSV)", data=df.to_csv(index=False).encode(), file_name=f"pacing_plan_{int(distance)}m.csv", mime="text/csv")

    else:
        st.markdown('<div class="sf-card">', unsafe_allow_html=True)
        st.markdown("### Post-race inputs")
        c5,c6,c7 = st.columns([1,1,1])
        unit = c5.radio("Your split unit", ["50","100"], horizontal=True, index=0)
        pb50 = c6.number_input("50m Personal Best (s)", min_value=0.0, step=0.01, value=24.00, format="%.2f")
        pool_len = c7.selectbox("Pool length", [25,50], index=1)
        raw = st.text_area("Paste your splits (use ';' or ',' or spaces)", placeholder="33;38;42;40;47;49;40;38")
        act = st.button("Analyze race", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

        if act:
            splits = coerce_splits_str_to_seconds_list(raw)
            if not splits:
                st.warning("Please paste valid splits.")
            else:
                if unit=="100":
                    splits = expand_100_splits_to_50(splits)
                details, metrics, tips = analyze_post_race(splits, float(pb50))
                st.success(f"Total: **{metrics['Total (mm:ss)']}**, Average per-50: **{metrics['Average per-50']}**")
                cA,cB,cC,cD = st.columns(4)
                cA.metric("Std dev (s)", metrics["Std dev (s)"])
                cB.metric("CV (%)", metrics["CV (%)"])
                cC.metric("Trend slope (s/50)", metrics["Slope (sec per 50)"])
                cD.metric("Laps (50m)", metrics["Laps (50m)"])
                st.dataframe(details, use_container_width=True, hide_index=True)
                safe_altair_chart(details, "Lap (50m)", "Split (s)", "Race Splits (per-50)")
                st.markdown("### Recommendations")
                for t in tips: st.write(f"- {t}")
                st.download_button("Download analysis (CSV)", data=details.to_csv(index=False).encode(), file_name=f"post_race_analysis_{int(distance)}m.csv", mime="text/csv")

def main():
    if "authed" not in st.session_state or not st.session_state["authed"]:
        login_or_register(); return
    with st.sidebar:
        st.write(f"Signed in as **{st.session_state.get('username','')}**")
    # Logout
    logout_button()
    # Main
    main_page()

if __name__ == "__main__":
    main()
