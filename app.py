import streamlit as st
import pandas as pd
import os
from PIL import Image
from base64 import b64encode
import plotly.express as px
import plotly.graph_objects as go

# --- App config ---
st.set_page_config(layout="wide")
st.title("Smart Charging Trade-off Explorer")

# --- Load experiment data ---
power_data = pd.read_csv("overall_power_side_results.csv")

# Convert to numeric
for col in ['energy_cost_all', 'total_energy_delivered', 'proportion_delivered', 'weight_obj_cost']:
    power_data[col] = pd.to_numeric(power_data[col], errors='coerce')

# Filter static mix
power_data = power_data[power_data["CUTOFF_TIME_FOR_RESULTS_MIXING"] == -1].copy()

# Compute cost per kWh
power_data["cost_per_kWh"] = power_data["energy_cost_all"] / (power_data["total_energy_delivered"] + 1e-8)
power_data["rounded_weight"] = power_data["weight_obj_cost"].round().astype(int)

# --- Plotly Pareto plot ---
st.subheader("Click on a Point to View Scenario Comparison")

fig = px.scatter(
    power_data,
    x="cost_per_kWh",
    y="proportion_delivered",
    color="Traffic-scenario",
    symbol="Traffic-scenario",
    hover_data=["rounded_weight", "Scenario", "Transformer-capacity"],
    labels={
        "cost_per_kWh": "Mean TOU Cost ($/kWh)",
        "proportion_delivered": "Energy Demand Met (%)"
    },
    title="Interactive Pareto Front (Click a point to explore)"
)

fig.update_traces(marker=dict(size=8, opacity=0.6))
fig.update_layout(height=400, legend=dict(font=dict(size=10)))

selected = st.plotly_chart(fig, use_container_width=True, click_events=True)

# --- Capture click event from Plotly ---
clicked_point = st.session_state.get("clicked_weight", None)

# Custom Streamlit Plotly click capture (works only in streamlit >= 1.29)
if "last_clicked" not in st.session_state:
    st.session_state.last_clicked = None

clicked = st.experimental_data_editor(pd.DataFrame(), key="plot_click")

if clicked is not None and "points" in clicked:
    for point in clicked["points"]:
        clicked_weight = point["customdata"][0]  # Extract rounded_weight
        st.session_state.last_clicked = clicked_weight

# Fallback if no point is clicked
selected_weight = st.session_state.last_clicked or 100

st.info(f"Showing results for selected weight: {selected_weight}")

# --- Custom function to auto-scale images ---
def display_image_autoscaled(path, caption=""):
    with open(path, "rb") as f:
        data = f.read()
        encoded = b64encode(data).decode()
        image_html = f"""
        <div style='max-width:100%; height:auto; text-align:center;'>
            <img src='data:image/jpeg;base64,{encoded}' style='width:100%; height:auto; border-radius:6px;' alt='Image'>
            <p style='font-size: small; color: gray;'>{caption}</p>
        </div>
        """
        st.markdown(image_html, unsafe_allow_html=True)

# --- Get matched scenarios ---
data_acc = power_data[(power_data["Traffic-scenario"] == "45-mins-accident-1-capacity-remaining-start-10am") &
                      (power_data["rounded_weight"] == selected_weight)]
data_nacc = power_data[(power_data["Traffic-scenario"] == "no-accident") &
                       (power_data["rounded_weight"] == selected_weight)]

cols_to_display = [
    "Traffic-scenario", "Transformer-capacity", "Scenario", "weight_obj_cost",
    "proportion_delivered", "total_energy_delivered", "total_energy_requested",
    "demands_fully_met", "energy_cost_all"
]

# --- Display both scenarios side-by-side ---
st.subheader("Scenario Comparison")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**No-Accident Scenario**")
    img_path = f"images/jpg_output/d_-1_no-accidentOffline-cap-1300-runnum-1_weight_{selected_weight}_page1.jpg"
    if os.path.exists(img_path):
        display_image_autoscaled(img_path, caption="No-Accident Scenario")
    else:
        st.warning("Image not found.")
    if not data_nacc.empty:
        st.dataframe(data_nacc[cols_to_display].transpose())

with col2:
    st.markdown("**Accident Scenario**")
    img_path = f"images/jpg_output/d_-1_45-mins-accident-1-capacity-remaining-start-10amOffline-cap-1300-runnum-1_weight_{selected_weight}_page1.jpg"
    if os.path.exists(img_path):
        display_image_autoscaled(img_path, caption="Accident Scenario")
    else:
        st.warning("Image not found.")
    if not data_acc.empty:
        st.dataframe(data_acc[cols_to_display].transpose())
