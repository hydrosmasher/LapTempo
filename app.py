import streamlit as st
import pandas as pd
import os
from swim_models import get_model_statuses, get_ready_models, predict_splits

# ==========================
#  UI Setup
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANNER_FILE = os.path.join(BASE_DIR, "Swim-Forge Banner.png")
LOGO_FILE = os.path.join(BASE_DIR, "logo.png")

st.set_page_config(page_title="SwimForge", page_icon=LOGO_FILE if os.path.exists(LOGO_FILE) else None, layout="wide")

# ==========================
#  Banner & Logo (safe loading)
# ==========================
try:
    if os.path.exists(BANNER_FILE):
        st.image(BANNER_FILE, use_container_width=True)
    else:
        st.warning("⚠️ Banner image not found. Please place 'Swim-Forge Banner.png' in the Swim-Forge folder.")
except Exception as e:
    st.warning(f"⚠️ Could not load banner image: {e}")

col1, col2 = st.columns([1, 6])
with col1:
    try:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, width=100)
        else:
            st.warning("⚠️ Logo not found. Please place 'logo.png' in the Swim-Forge folder.")
    except Exception as e:
        st.warning(f"⚠️ Could not load logo: {e}")
with col2:
    st.title("SwimForge")
    st.subheader("Where Science Shapes Speed")

# ==========================
# Sidebar Training Status
# ==========================
statuses = get_model_statuses()
st.sidebar.header("Model Training Progress")
for stroke, status in statuses.items():
    st.sidebar.write(f"{stroke}: {status}")

# ==========================
# App Functionalities
# ==========================
option = st.radio("Select Mode", ["Pre-Race", "Post-Race"])

if option == "Pre-Race":
    st.header("🏊 Pre-Race Preparation")
    pb_50 = st.number_input("Enter your 50m Personal Best (seconds)", min_value=20.0, max_value=60.0, step=0.01)
    target_time = st.number_input("Enter Target Event Time (seconds)", min_value=20.0, step=0.01)
    event_distance = st.selectbox("Event Distance (m)", [50, 100, 200, 400, 800, 1500])

    if st.button("Generate Pre-Race Plan"):
        avg_split = target_time / (event_distance / 50)
        st.success(f"To hit {target_time:.2f}s in {event_distance}m, aim for ~{avg_split:.2f}s per 50m.")
        if avg_split > pb_50:
            st.warning("Target pace is slower than your PB → push harder!")
        else:
            st.info("Target pace is faster than PB → requires speed focus.")

elif option == "Post-Race":
    st.header("🏅 Post-Race Analysis")

    ready_strokes = get_ready_models()
    if not ready_strokes:
        st.warning("⚠️ No models are ready yet. Please wait for training to finish.")
    else:
        stroke = st.selectbox("Select Stroke", ready_strokes)
        split_choice = st.radio("Split Type", ["50m", "100m"])
        num_splits = st.number_input(f"How many {split_choice} splits?", min_value=1, step=1)
        pb_50 = st.number_input("Enter your 50m PB (seconds)", min_value=20.0, max_value=60.0, step=0.01)

        splits = []
        for i in range(int(num_splits)):
            splits.append(st.number_input(f"Lap {i+1} ({split_choice})", min_value=20.0, step=0.01, key=f"lap{i}"))

        if st.button("Analyze Splits"):
            df = predict_splits(stroke, splits)
            if df is None:
                st.warning(f"⚠️ Model for {stroke} not ready yet.")
            else:
                st.dataframe(df.style.applymap(
                    lambda v: "background-color: #ff9999" if isinstance(v, (int, float)) and v > 0 else "background-color: #99ff99" if isinstance(v, (int, float)) else "",
                    subset=["Δ (Actual - Predicted)"]
                ), use_container_width=True)

# ==========================
# Sidebar Utilities
# ==========================
st.sidebar.header("Utilities")
if st.sidebar.button("Reset App"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

if st.sidebar.button("Shutdown App"):
    st.warning("App will stop after execution.")
    os._exit(0)
