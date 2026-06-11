# dashboard/app.py
import streamlit as st
import pandas as pd
import numpy as np
import time
from simulator.engine import Simulator
from models.predict import Predictor
from llm.vllm_client import VLLMClient
from datetime import datetime, timedelta
import plotly.graph_objects as go
import threading
import joblib
import os

st.set_page_config(page_title="Hospital Digital Twin", layout="wide", initial_sidebar_state="expanded")
st.markdown("<style> .big-font { font-size:20px; } </style>", unsafe_allow_html=True)

# Sidebar controls
st.sidebar.title("Simulation Controls")
seed = st.sidebar.number_input("Random seed", value=42, step=1)
hours = st.sidebar.slider("Simulate hours", 6, 72, 24)
horizon = st.sidebar.selectbox("Forecast horizon (hours)", [1,2,4,6], index=2)
inject_surge = st.sidebar.checkbox("Inject surge at hour 4", value=False)
start_now = st.sidebar.button("Start Simulation")

# Initialize components
if "sim" not in st.session_state:
    st.session_state.sim = Simulator(seed=seed)
    st.session_state.df = None
    st.session_state.pred = None
    st.session_state.alerts = []

predictor = None
if os.path.exists("models/xgb_model.pkl"):
    predictor = Predictor("models/xgb_model.pkl")
llm = VLLMClient()

# Layout
col1, col2 = st.columns([3,1])
with col1:
    st.header("Hospital Operations Digital Twin")
    chart_area = st.empty()
    table_area = st.empty()
with col2:
    st.header("Alerts")
    alerts_area = st.empty()
    st.markdown("**Scenario**")
    if st.button("Run surge scenario (demo)"):
        inject_surge = True
        start_now = True

def run_and_update():
    sim = st.session_state.sim
    df = sim.run_hours(hours=hours, surge_hours=[4] if inject_surge else None)
    st.session_state.df = df
    # Save for model training/demo
    df.to_csv("sim_data.csv", index=False)
    # Predictions per dept
    preds = {}
    for dept in ["ED","ICU","Ward"]:
        if predictor:
            # create a small window for predictor
            pred_val = predictor.predict_horizon(df)
        else:
            # fallback simple linear extrapolation
            pred_val = df[f"{dept}_count"].iloc[-1] * 1.1
        preds[dept] = pred_val
    st.session_state.pred = preds

    # Build chart
    fig = go.Figure()
    for d in ["ED","ICU","Ward"]:
        fig.add_trace(go.Scatter(x=df["time"], y=df[f"{d}_count"], name=f"{d} occupancy", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=[df["time"].iloc[-1], df["time"].iloc[-1] + pd.Timedelta(hours=horizon)],
                                 y=[df[f"{d}_count"].iloc[-1], preds[d]],
                                 name=f"{d} forecast", mode="lines", line=dict(dash="dash")))
    fig.update_layout(height=500, legend=dict(orientation="h"))
    chart_area.plotly_chart(fig, use_container_width=True)

    # Table
    latest = df.iloc[-1]
    table = pd.DataFrame({
        "department": ["ED","ICU","Ward"],
        "current_count": [latest["ED_count"], latest["ICU_count"], latest["Ward_count"]],
        "predicted_count": [preds["ED"], preds["ICU"], preds["Ward"]],
    })
    table["pred_pct_change"] = ((table["predicted_count"] - table["current_count"]) / table["current_count"].replace(0,1)) * 100
    table_area.dataframe(table)

    # LLM alerts with guardrail: require pct>20% and predicted_count>capacity threshold
    alerts = []
    for _, row in table.iterrows():
        pct = row["pred_pct_change"]
        dept = row["department"]
        current = int(row["current_count"])
        pred = float(row["predicted_count"])
        staff = latest[f"{dept}_staff"]
        # guardrail: require both pct>20 and slope positive
        slope = df[f"{dept}_count"].diff().iloc[-3:].mean()
        if pct > 20 and slope > 0:
            text = llm.generate_alert(dept, current, pred, pct, horizon, staff, reason="xgboost+trend")
            alerts.append(text)
    st.session_state.alerts = alerts
    alerts_area.write("\n\n".join(alerts) if alerts else "No critical alerts.")

if start_now:
    with st.spinner("Running simulation and forecasts..."):
        run_and_update()
else:
    st.info("Configure controls and press Start Simulation to run the digital twin.")

# Export / demo helpers
st.sidebar.markdown("---")
if st.sidebar.button("Train model from sim data (quick)"):
    st.sidebar.info("Training XGBoost on sim_data.csv (may take ~1 min)")
    import subprocess
    subprocess.run(["python","models/train_xgb.py","--data","sim_data.csv","--out","models/xgb_model.pkl"], check=False)
    st.sidebar.success("Training started; refresh after completion.")
