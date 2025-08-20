# SwimForge – Full App with Reset & Close buttons, Banner/Logo, Secure Auth
from __future__ import annotations
import os, math, json
from typing import List, Tuple, Dict
from datetime import date, datetime
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except Exception:
    FERNET_AVAILABLE = False

try:
    import bcrypt
    HAS_BCRYPT = True
except Exception:
    HAS_BCRYPT = False

APP_TITLE = "SwimForge"
APP_TAGLINE = "Where Science Shapes Speed"
POWERED_BY = "Powered by HydroSmasher"

ASSETS_BANNER = "assets/banner.png"
ASSETS_LOGO = "assets/logo.png"

st.set_page_config(page_title=APP_TITLE, page_icon="🏊", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {padding-top: 0rem; padding-bottom: 3rem; max-width: 1200px;}
.hero { border-radius: 18px; padding: 16px 20px; margin: 14px 0 18px 0;
  background: linear-gradient(135deg, #0D1A35 0%, #0B1430 60%, #0A122C 100%);
  border: 1px solid rgba(120,150,255,0.12); text-align: center; }
.hero h1 { margin: 8px 0 0 0; font-size: 40px;}
.hero .sub { margin-top: 4px; opacity: 0.9;}
.hero .powered { margin-top: 2px; font-size: 12px; opacity: 0.65;}
.sf-card { background: rgba(255,255,255,0.02); border: 1px solid rgba(120,150,255,0.12);
  border-radius: 16px; padding: 18px; margin-bottom: 16px;}
.stButton>button { border-radius: 12px; padding: 10px 16px; font-weight: 600;
  border: 1px solid rgba(120,150,255,0.25);}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- Auth utils ----------
USERS_PATH_PLAIN = os.path.join(".data", "users.json")
USERS_PATH_ENC = os.path.join(".data", "users.enc")

def _get_fernet():
    if not FERNET_AVAILABLE: return None
    key = None
    try:
        if "auth" in st.secrets and "fernet_key" in st.secrets["auth"]:
            key = st.secrets["auth"]["fernet_key"]
    except Exception: pass
    if not key: key = os.getenv("FERNET_KEY", "")
    if not key: return None
    try: return Fernet(key.encode() if not key.startswith("gAAAA") else key)
    except Exception: return None

def _bcrypt_hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()

def _bcrypt_check(pw: str, hashed: str) -> bool:
    try: return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception: return False

def _load_users() -> Dict[str, Dict]:
    cipher = _get_fernet()
    if cipher and os.path.exists(USERS_PATH_ENC):
        try:
            with open(USERS_PATH_ENC,"rb") as f: data = cipher.decrypt(f.read())
            return json.loads(data.decode())
        except Exception: return {}
    if os.path.exists(USERS_PATH_PLAIN):
        try:
            with open(USERS_PATH_PLAIN,"r",encoding="utf-8") as f: return json.load(f)
        except Exception: return {}
    return {}

def _save_users(users: Dict[str, Dict]):
    os.makedirs(".data", exist_ok=True)
    payload = json.dumps(users, ensure_ascii=False).encode()
    cipher = _get_fernet()
    if cipher:
        with open(USERS_PATH_ENC,"wb") as f: f.write(cipher.encrypt(payload))
        if os.path.exists(USERS_PATH_PLAIN): os.remove(USERS_PATH_PLAIN)
    else:
        with open(USERS_PATH_PLAIN,"w",encoding="utf-8") as f: f.write(payload.decode())

def register_user(username:str,password:str)->Tuple[bool,str]:
    u=(username or "").strip().lower()
    if not u or " " in u or len(u)<3: return False,"Username too short or invalid."
    if len(password)<8: return False,"Password must be at least 8 chars."
    if not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password):
        return False,"Password must include letters and numbers."
    users=_load_users()
    if u in users: return False,"Username already exists."
    users[u]={"pw_hash":_bcrypt_hash(password),"created_at":datetime.utcnow().isoformat()+"Z"}
    _save_users(users)
    return True,"Account created. You can now sign in."

def authenticate(username:str,password:str)->bool:
    u=(username or "").strip().lower()
    users=_load_users()
    return u in users and _bcrypt_check(password,users[u]["pw_hash"])

# ---------- Core pacing ----------
def parse_time_to_seconds(s:str)->float:
    s=str(s).strip()
    if not s: return math.nan
    if ":" in s:
        parts=s.split(":")
        if len(parts)==3: h,m,sec=parts; return int(h)*3600+int(m)*60+float(sec)
        if len(parts)==2: m,sec=parts; return int(m)*60+float(sec)
    return float(s)

def format_seconds(t:float)->str:
    if t is None or (isinstance(t,float) and (math.isnan(t) or math.isinf(t))): return ""
    t=float(t); m=int(t//60); s=t-60*m
    return f"{m}:{s:05.2f}" if m>0 else f"{s:.2f}s"

def coerce_splits_str_to_seconds_list(s:str):
    if not s: return []
    for d in [";",",","\n","\t"]: s=s.replace(d," ")
    return [parse_time_to_seconds(x) for x in s.split() if x.strip()]

def expand_100_splits_to_50(lst): out=[]; [out.extend([s/2,s/2]) for s in lst]; return out

def safe_altair_chart(df,x,y,title):
    chart=alt.Chart(df).mark_line(point=True).encode(x=x,y=y,tooltip=[x,y]).properties(title=title).interactive()
    st.altair_chart(chart,use_container_width=True)

def pacing_plan(distance_m:int,target_time_s:float,pb50_s:float|None=None):
    n=int(distance_m//50)
    if n<=0: return []
    trend=np.full(n,target_time_s/n)
    if pb50_s and pb50_s>0:
        floor=0.95*pb50_s if distance_m>=200 else 0.90*pb50_s
        trend=np.maximum(trend,floor)
        trend=trend*(target_time_s/trend.sum())
    return trend.tolist()

def analyze_post_race(splits,pb50):
    s=np.array(splits,float); n=len(s)
    total=float(s.sum()); mean=float(s.mean())
    stdev=float(s.std(ddof=1)) if n>1 else 0.0
    cv=(stdev/mean*100.0) if mean>0 else 0.0
    slope=float(np.polyfit(np.arange(n),s,1)[0]) if n>=2 else 0.0
    fastest=float(s.min()) if n else math.nan
    slowest=float(s.max()) if n else math.nan
    delta_vs_mean=s-mean
    delta_vs_pb=s-(pb50 if (pb50 and pb50>0) else np.nan)
    pct_from_best=(s-fastest)/fastest*100.0 if fastest>0 else np.zeros(n)
    details=pd.DataFrame({"Lap (50m)":np.arange(1,n+1),
        "Split (s)":np.round(s,2),
        "Split (mm:ss)":[format_seconds(x) for x in s],
        "Δ vs mean (s)":np.round(delta_vs_mean,2),
        "Δ vs 50 PB (s)":np.round(delta_vs_pb,2),
        "% from fastest (%)":np.round(pct_from_best,2),
        "Cumulative (mm:ss)":[format_seconds(sum(s[:i+1])) for i in range(n)],})
    metrics={"Total (mm:ss)":format_seconds(total),
        "Average per-50":format_seconds(mean),
        "Std dev (s)":round(stdev,2),
        "CV (%)":round(cv,2),
        "Slope (sec per 50)":round(slope,3),
        "Fastest 50":format_seconds(fastest),
        "Slowest 50":format_seconds(slowest),
        "Laps (50m)":n}
    tips=[]
    if n>=2:
        if s[0]<mean*0.94: tips.append("Opening too fast.")
        elif s[0]>mean*1.05: tips.append("Opening too conservative.")
    if n>=4 and s[-1]<=mean*0.98: tips.append("Strong finish.")
    elif n>=4 and s[-1]>=mean*1.05: tips.append("Fade at the end.")
    if cv>=3.0: tips.append("High variability. Focus even pacing.")
    else: tips.append("Good consistency.")
    if slope>0.1: tips.append("Splits trend slower.")
    elif slope<-0.1: tips.append("Splits trend faster.")
    if pb50 and pb50>0:
        if (s<0.95*pb50).any(): tips.append("Some splits near raw 50 PB.")
        if (s>1.20*pb50).any(): tips.append("Splits >120% of PB.")
    return details,metrics,tips

# ---------- UI helpers ----------
def show_banner_logo():
    if os.path.exists(ASSETS_BANNER): st.image(ASSETS_BANNER,use_column_width=True)
    if os.path.exists(ASSETS_LOGO): st.sidebar.image(ASSETS_LOGO,width=72)

def reset_app():
    st.session_state.clear(); st.rerun()

def close_app():
    st.session_state.clear()
    st.markdown("## 👋 App closed. Please stop the Streamlit server manually (Ctrl+C).")
    st.stop()

def login_or_register():
    show_banner_logo()
    tab1,tab2=st.tabs(["Sign in","Create account"])
    with tab1:
        with st.form("login"):
            u=st.text_input("Username"); p=st.text_input("Password",type="password")
            s=st.form_submit_button("Sign in")
        if s:
            if authenticate(u,p):
                st.session_state["authed"]=True; st.session_state["username"]=u; st.rerun()
            else: st.error("Invalid login")
    with tab2:
        with st.form("register",clear_on_submit=True):
            u=st.text_input("New username"); p1=st.text_input("New password",type="password"); p2=st.text_input("Confirm",type="password")
            agree=st.checkbox("I understand my credentials are stored hashed (and encrypted if enabled).")
            s=st.form_submit_button("Create account")
        if s:
            if not agree: st.error("Confirm checkbox"); return
            if p1!=p2: st.error("Passwords mismatch"); return
            ok,msg=register_user(u,p1); (st.success if ok else st.error)(msg)

def main_page():
    show_banner_logo()
    st.header("🛟 Race Split")
    st.caption("Pre-race optimal splits and post-race analysis")
    c1,c2,c3,c4=st.columns([1,1,1,1])
    race_day=c1.date_input("Race day",value=date.today())
    stroke=c2.selectbox("Stroke",["free","back","breast","fly","IM"])
    distance=c3.number_input("Distance (m)",50,1500,50,50)
    mode=c4.radio("Mode",["Pre-race","Post-race"])
    if mode=="Pre-race":
        pb50=st.number_input("50m PB (s)",0.0,step=0.01,value=24.0)
        target_total=st.number_input("Target total (s)",0.0,step=0.01,value=120.0)
        if st.button("Compute splits"):
            splits=pacing_plan(distance,target_total,pb50)
            df=pd.DataFrame({"Lap":np.arange(1,len(splits)+1),
                "Split (s)":np.round(splits,2),
                "Split (mm:ss)":[format_seconds(x) for x in splits]})
            st.dataframe(df,hide_index=True)
            safe_altair_chart(df,"Lap","Split (s)","Pacing plan")
    else:
        unit=st.radio("Your split unit",["50","100"])
        pb50=st.number_input("50m PB (s)",0.0,step=0.01,value=24.0)
        raw=st.text_area("Splits")
        if st.button("Analyze race"):
            splits=coerce_splits_str_to_seconds_list(raw)
            if unit=="100": splits=expand_100_splits_to_50(splits)
            details,metrics,tips=analyze_post_race(splits,pb50)
            st.dataframe(details,hide_index=True)
            st.json(metrics)
            for t in tips: st.write("-",t)

def sidebar_controls():
    if "username" in st.session_state:
        st.sidebar.write("Signed in as",st.session_state["username"])
    if st.sidebar.button("🔄 Reset App"): reset_app()
    if st.sidebar.button("❌ Close App"): close_app()
    if st.sidebar.button("Log out"): reset_app()

def main():
    if "authed" not in st.session_state or not st.session_state["authed"]:
        login_or_register(); return
    sidebar_controls()
    main_page()

if __name__=="__main__":
    main()
