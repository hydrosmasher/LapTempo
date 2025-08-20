# SwimForge – App with Reset & Close buttons
from __future__ import annotations
import os, math, json
from typing import List, Tuple, Dict
from datetime import date, datetime
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

try:
    import bcrypt
    HAS_BCRYPT = True
except Exception:
    HAS_BCRYPT = False

st.set_page_config(page_title="SwimForge", page_icon="🏊", layout="wide")

ASSETS_BANNER = "assets/banner.png"
ASSETS_LOGO = "assets/logo.png"

# ============================= Utilities =============================
def reset_app():
    st.session_state.clear()
    st.rerun()

def close_app():
    st.session_state.clear()
    st.markdown("## 👋 App closed. Please stop the Streamlit server manually (Ctrl+C in terminal).")
    st.stop()

def show_sidebar_controls():
    if os.path.exists(ASSETS_LOGO):
        st.sidebar.image(ASSETS_LOGO, width=72)
    if "username" in st.session_state:
        st.sidebar.write(f"Signed in as **{st.session_state['username']}**")
    if st.sidebar.button("🔄 Reset App"):
        reset_app()
    if st.sidebar.button("❌ Close App"):
        close_app()
    if st.sidebar.button("Log out"):
        reset_app()

# ... rest of your app logic here (login_or_register, main_page, etc.) ...
