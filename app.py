# app.py — Swim Forge (reverted UI: no page backgrounds, keeps banner/logo & theme)

import os
from pathlib import Path
from datetime import date
from io import BytesIO

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Local modules (must exist in your repo)
from src.auth import register, login
from src.pacing_simulator import RuleBasedPacer, DLPacingPredictor
from src.utils.helpers import parse_semicolon_splits, even_split

# ---------- Page config ----------
st.set_page_config(page_title="Swim Forge", page_icon="🏊", layout="wide")

# ---------- THEME (pool-styled, no image backgrounds) ----------
def inject_theme_css():
    st.markdown(
        """
        <style>
        /* Sidebar soft gradient */
        section[data-testid="stSidebar"] > div {
          background: linear-gradient(180deg, #EAF0FF 0%, #F6F9FF 100%);
        }

        /* Buttons (primary + downloads) */
        .stButton>button, .stDownloadButton>button {
          background: linear-gradient(135deg, #7DD3FC 0%, #A78BFA 100%);
          color: white !important;
          border: none;
          border-radius: 10px;
          padding: 0.5rem 1rem;
          box-shadow: 0 6px 14px rgba(90,102,241,0.15);
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
          filter: brightness(1.03);
          box-shadow: 0 8px 18px rgba(90,102,241,0.25);
        }
        .stButton>button:active, .stDownloadButton>button:active { transform: translateY(1px); }

        /* Inputs: subtle rounding */
        div[data-baseweb="select"] > div,
        .stTextInput>div>div>input,
        .stNumberInput input,
        .stDateInput input,
        .stRadio > div,
        .stTextArea textarea {
          border-radius: 10px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

inject_theme_css()

# ---------- Session bootstrap ----------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- Helpers ----------
def _dl_weights_available() -> bool:
    pt_ok = os.path.exists("models/pacing_head.pt") and os.path.getsize("models/pacing_head.pt") > 0
    pkl_ok = os.path.exists("models/pacing_head.pkl") and os.path.getsize("models/pacing_head.pkl") > 0
    return pt_ok or pkl_ok

def create_pdf_report(metadata: dict, chart_pngs: list[bytes]) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Swim Forge Race Report")

    c.setFont("Helvetica", 10)
    y = height - 80
    for key, val in metadata.items():
        c.drawString(50, y, f"{key}: {val}")
        y -= 12

    for img_bytes in chart_pngs:
        if not img_bytes:
            continue
        img_stream = BytesIO(img_bytes)
        c.drawImage(img_stream, 50, y - 200, width=500, height=200, preserveAspectRatio=True, anchor="sw")
        y -= 220

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def chart_to_png(chart, scale: int = 2):
    try:
        import vl_convert as vlc
        spec = chart.to_dict()
        return vlc.vegalite_to_png(spec, scale=scale)
    except Exception:
        st.warning("PNG export requires 'vl-convert-python'. Run: pip install vl-convert-python")
        return None

def show_banner():
    png_path = Path("assets/banner.png")
    svg_path = Path("assets/banner.svg")
    if png_path.exists():
        st.image(str(png_path), use_container_width=True)
    elif svg_path.exists():
        svg_content = svg_path.read_text(encoding="utf-8")
        st.markdown(
            f"""
            <div style="max-width:100%; max-height:180px; overflow:hidden; display:flex; justify-content:center;">
              {svg_content}
            </div>
            """,
            unsafe_allow_html=True,
        )

def show_logo():
    png_path = Path("assets/logo.png")
    svg_path = Path("assets/logo.svg")
    if png_path.exists():
        st.sidebar.image(str(png_path), use_container_width=True)
    elif svg_path.exists():
        svg_content = svg_path.read_text(encoding="utf-8")
        st.sidebar.markdown(
            f"""
            <div style="max-width:100%; max-height:60px; overflow:hidden; display:flex; justify-content:center;">
              {svg_content}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------- Pages ----------
def landing_page():
    show_banner()
    st.title("🏊 Swim Forge")
    st.subheader("Competitive pacing • Race analysis • Training tools")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            le = st.text_input("Email", placeholder="you@gmail.com")
            lp = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
        if submitted:
            ok, msg, user = login(le, lp)
            if ok:
                st.session_state.user = user
                st.session_state.page = "Race Split (Pre/Post)"
                st.success(f"{msg} — Welcome back, {user['email']}")
                st.rerun()
            else:
                st.error(msg)

    with tab_register:
        with st.form("register_form", clear_on_submit=False):
            re = st.text_input("Email", placeholder="you@gmail.com", key="re")
            rp = st.text_input("Password", type="password", key="rp")
            submitted_r = st.form_submit_button("Create account")
        if submitted_r:
            ok, msg = register(re, rp)
            if ok:
                st.success(msg + " You can now log in.")
            else:
                st.error(msg)

def app_nav():
    if st.session_state.user and "page" not in st.session_state:
        st.session_state.page = "Race Split (Pre/Post)"

    show_logo()
    st.sidebar.header("Account")
    user = st.session_state.user
    st.sidebar.success(f"Logged in as: {user['email']}")
    st.sidebar.caption(f"Athlete ID: {user['athlete_id']}")

    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("Reset App"):
        st.session_state.clear()
        st.success("App state cleared. Reloading…")
        st.rerun()

    if st.sidebar.button("Close App"):
        st.info("Session terminated. You can close the browser tab.")
        st.stop()

    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["Race Split (Pre/Post)", "Home (About)"], index=0, key="page")

    if page == "Home (About)":
        st.title("🏊 Swim Forge — Home")
        st.write(
            """
            Welcome to **Swim Forge**. Use the sidebar to navigate to **Race Split (Pre/Post)**.
            This build preserves the registration & login flow and includes DL/ML pacing where available.
            """
        )
    else:
        race_split_page()

def race_split_page():
    show_banner()
    st.title("🏊 Race Split")
    st.caption("Pre-race optimal splits and post-race analysis")

    st.sidebar.header("Model")
    weights_available = _dl_weights_available()
    use_dl = st.sidebar.checkbox(
        "Use Deep Learning Pacing Model (if available)",
        value=weights_available,
    )
    if use_dl and not weights_available:
        st.sidebar.info("No model weights found (.pt or .pkl). Falling back to rule-based.")
        use_dl = False

    rb = RuleBasedPacer()
    dl = None
    if use_dl:
        try:
            dl = DLPacingPredictor(weights_path="models/pacing_head.pt")
            if not dl.available:
                st.sidebar.warning("DL model not available; using rule-based instead.")
                dl = None
        except Exception as e:
            st.sidebar.warning(f"DL init failed: {e}")
            dl = None

    st.subheader("Race Setup")
    col1, col2, col3, col4 = st.columns(4)
    race_day = col1.date_input("Race day", value=date.today())
    stroke = col2.selectbox("Stroke", ["free", "fly", "back", "breast", "im"])
    distance = col3.selectbox("Distance (m)", [50, 100, 200, 400, 800, 1500])
    mode = col4.radio("Mode", ["Pre-race", "Post-race"], horizontal=True)

    if mode == "Pre-race":
        st.markdown("### Pre-race inputs")
        p1, p2, p3 = st.columns(3)
        pb50 = p1.number_input("50m Personal Best (s)", min_value=10.0, max_value=60.0, value=24.0, step=0.01)
        target_time = p2.number_input("Target time for event (s)", min_value=20.0, max_value=6000.0, value=120.0, step=0.01)
        pool_m = p3.selectbox("Pool length", [50, 25], index=0)

        if st.button("Compute optimal splits"):
            if use_dl and dl:
                splits = dl.predict_optimal_splits(
                    distance=distance, stroke=stroke, target_time=target_time, pool_m=pool_m
                )
            else:
                splits = rb.predict_optimal_splits(
                    distance=distance, stroke=stroke, target_time=target_time, pb50=pb50
                )

            st.success("Optimal per-50 splits (s)")
            st.write(splits)
            st.bar_chart(splits)

            df_pre = pd.DataFrame({"Lap": list(range(1, len(splits) + 1)), "Optimal": splits})
            chart_pre = (
                alt.Chart(df_pre)
                .mark_line(point=True)
                .encode(x="Lap:O", y="Optimal:Q")
                .properties(width=600, height=300, title="Optimal per-50 splits (line chart)")
            )
            st.altair_chart(chart_pre, use_container_width=True)
            pre_png = chart_to_png(chart_pre)
            if pre_png:
                st.download_button(
                    "Download Pre-race PNG",
                    data=pre_png,
                    file_name="pre_race_optimal.png",
                    mime="image/png",
                )

    if mode == "Post-race":
        st.markdown("### Post-race inputs")
        q1, q2 = st.columns(2)
        unit = q1.selectbox("Input split unit", [50, 100], index=0)
        splits_text = q2.text_area(
            "Enter splits separated by ';' (supports mm:ss too)",
            value="; ".join(["30.5"] * (distance // unit)),
        )
        pool_m = st.selectbox("Pool length", [50, 25], index=0)
        target_time = st.number_input(
            "Target time for comparison (s)",
            min_value=0.0,
            max_value=6000.0,
            value=0.0,
            step=0.01,
            help="Optional; used to synthesize an optimal if none.",
        )

        if st.button("Analyze race"):
            raw = parse_semicolon_splits(splits_text)
            if unit == 100 and raw is not None:
                actual_50 = []
                for s in raw:
                    actual_50.extend([round(s / 2, 2), round(s / 2, 2)])
            else:
                actual_50 = raw

            if not actual_50 or len(actual_50) != distance // 50:
                st.error(
                    f"Expected {distance//50} splits at 50m granularity, got {len(actual_50) if actual_50 else 0}."
                )
            else:
                if use_dl and dl and target_time > 0:
                    optimal_50 = dl.predict_optimal_splits(
                        distance=distance, stroke=stroke, target_time=target_time, pool_m=pool_m
                    )
                else:
                    total = sum(actual_50) if target_time <= 0 else target_time
                    optimal_50 = even_split(total, distance)

                df = pd.DataFrame(
                    {"Lap": list(range(1, len(actual_50) + 1)), "Actual": actual_50, "Optimal": optimal_50}
                )
                df["Delta"] = df["Actual"] - df["Optimal"]

                chart_lines = (
                    alt.Chart(df)
                    .transform_fold(["Actual", "Optimal"], as_=["Type", "Time"])
                    .mark_line(point=True)
                    .encode(x="Lap:O", y="Time:Q", color="Type:N")
                    .properties(width=600, height=300, title="Actual vs Optimal per-50 splits")
                )

                chart_delta = (
                    alt.Chart(df)
                    .mark_bar()
                    .encode(
                        x="Lap:O",
                        y="Delta:Q",
                        color=alt.condition("datum.Delta <= 0", alt.value("green"), alt.value("red")),
                    )
                    .properties(width=600, height=300, title="Delta (Actual - Optimal)")
                )

                st.altair_chart(chart_lines, use_container_width=True)
                st.altair_chart(chart_delta, use_container_width=True)

                turn_issues = []
                for i in range(1, len(df) - 1):
                    if (i + 1) % 2 == 1 and df.loc[i, "Delta"] > 0.6:
                        turn_issues.append(
                            f"Lap {i+1}: Slow after turn (+{df.loc[i, 'Delta']:.2f}s) — work on breakout and push-offs."
                        )

                if turn_issues:
                    st.subheader("Turn Insights")
                    for tip in turn_issues:
                        st.markdown(f"- {tip}")

                lines_png = chart_to_png(chart_lines)
                delta_png = chart_to_png(chart_delta)
                chart_list = [b for b in [lines_png, delta_png] if b]

                pdf_buffer = create_pdf_report(
                    metadata={"Race Day": race_day, "Stroke": stroke, "Distance": distance, "Pool": pool_m},
                    chart_pngs=chart_list,
                )

                if lines_png:
                    st.download_button(
                        "Download Actual vs Optimal PNG",
                        data=lines_png,
                        file_name="actual_vs_optimal.png",
                        mime="image/png",
                    )
                if delta_png:
                    st.download_button(
                        "Download Delta PNG",
                        data=delta_png,
                        file_name="delta_chart.png",
                        mime="image/png",
                    )
                st.download_button(
                    "Download PDF Report", data=pdf_buffer, file_name="race_report.pdf", mime="application/pdf"
                )

# ---------- Router ----------
if st.session_state.user is None:
    landing_page()
else:
    app_nav()