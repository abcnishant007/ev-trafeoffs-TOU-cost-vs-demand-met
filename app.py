import streamlit as st
import pandas as pd
import os
from PIL import Image
from base64 import b64encode
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# --- App config ---
st.set_page_config(layout="wide")
st.title("Smart Charging Trade-off Explorer")

# --- Load and preprocess data ---
power_data = pd.read_csv("overall_power_side_results.csv")

for col in ['energy_cost_all', 'total_energy_delivered', 'proportion_delivered', 'weight_obj_cost']:
    power_data[col] = pd.to_numeric(power_data[col], errors='coerce')

power_data = power_data[power_data["CUTOFF_TIME_FOR_RESULTS_MIXING"] == -1].copy()
power_data["cost_per_kWh"] = power_data["energy_cost_all"] / (power_data["total_energy_delivered"] + 1e-8)
power_data["rounded_weight"] = power_data["weight_obj_cost"].round().astype(int)
power_data["ratio_TOU_TED"] = power_data["weight_obj_cost"] / 30

# --- Abbreviation note ---
st.markdown("""
> **Note:**  
> - **TOU** = *Time-of-Use energy cost weighting*  
> - **TED** = *Total Energy Delivered weighting*  
> - TED is fixed at 30.  
> - The ratio shown below is \\( \\frac{W_{\\text{TOU}}}{W_{\\text{TED}}} \\)
""")

# --- Pareto plot ---
st.subheader("Click on a Point to View Scenario Comparison")

fig = go.Figure()

marker_map = {
    "no-accident": "circle",
    "45-mins-accident-1-capacity-remaining-start-10am": "x"
}

for scenario, group in power_data.groupby("Traffic-scenario"):
    marker_symbol = marker_map.get(scenario, "circle")
    fig.add_trace(go.Scatter(
        x=group["cost_per_kWh"],
        y=group["proportion_delivered"],
        mode="markers",
        name=scenario,
        marker=dict(size=1, opacity=0.6, symbol=marker_symbol),
        customdata=group["weight_obj_cost"],
        hovertemplate="Ratio (TOU/TED): %{customdata:.2f}<extra></extra>",
    ))

for scenario, group in power_data.groupby("Traffic-scenario"):
    group_sorted = group.sort_values("cost_per_kWh")
    pareto = []
    max_y = -float("inf")
    for _, row in group_sorted.iterrows():
        if row["proportion_delivered"] > max_y:
            pareto.append(row)
            max_y = row["proportion_delivered"]
    pareto_df = pd.DataFrame(pareto)
    fig.add_trace(go.Scatter(
        x=pareto_df["cost_per_kWh"],
        y=pareto_df["proportion_delivered"],
        mode="lines",
        name=f"{scenario} Pareto",
        line=dict(width=2),
        hoverinfo="skip"
    ))

fig.update_layout(
    xaxis=dict(title="TOU Cost ($/kWh)", range=[0, 0.15]),
    yaxis=dict(title="Energy Demand Met (%)", range=[65, 105]),
    height=360,
    legend=dict(font=dict(size=10)),
    margin=dict(l=10, r=10, t=30, b=20)
)

# --- Click handling ---
if "last_clicked" not in st.session_state:
    st.session_state.last_clicked = 100  # default

clicked_points = plotly_events(fig, click_event=True, override_height=360)

if clicked_points and isinstance(clicked_points[0], dict) and "customdata" in clicked_points[0]:
    try:
        st.session_state.last_clicked = int(clicked_points[0]["customdata"])
    except Exception:
        pass

selected_weight = st.session_state.last_clicked
st.markdown(f"### 🔍 Selected TOU/TED Ratio: **{selected_weight / 30:.2f}** (Weight: {selected_weight})")

# --- Display helper ---
def display_image_autoscaled(path, caption=""):
    with open(path, "rb") as f:
        encoded = b64encode(f.read()).decode()
        html = f"""
        <div style='max-width:100%; height:auto; text-align:center;'>
            <img src='data:image/jpeg;base64,{encoded}' style='width:100%; height:auto; border-radius:6px;' alt='Image'>
            <p style='font-size: small; color: gray;'>{caption}</p>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

# --- Scenario filtering ---
data_acc = power_data[
    (power_data["Traffic-scenario"] == "45-mins-accident-1-capacity-remaining-start-10am") &
    (power_data["rounded_weight"] == selected_weight)
]
data_nacc = power_data[
    (power_data["Traffic-scenario"] == "no-accident") &
    (power_data["rounded_weight"] == selected_weight)
]

cols_to_display = [
    "Traffic-scenario", "Transformer-capacity", "Scenario", "ratio_TOU_TED",
    "proportion_delivered", "total_energy_delivered", "total_energy_requested",
    "demands_fully_met", "energy_cost_all"
]

# --- Side-by-side scenario comparison ---
st.subheader("Scenario Comparison")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**No-Accident Scenario**")
    path_nacc = f"images/jpg_output/d_-1_no-accidentOffline-cap-1300-runnum-1_weight_{selected_weight}_page1.jpg"
    if os.path.exists(path_nacc):
        display_image_autoscaled(path_nacc, caption="No-Accident Scenario")
    else:
        st.warning("Image not found.")
    if not data_nacc.empty:
        st.dataframe(data_nacc[cols_to_display].transpose())

with col2:
    st.markdown("**Accident Scenario**")
    path_acc = f"images/jpg_output/d_-1_45-mins-accident-1-capacity-remaining-start-10amOffline-cap-1300-runnum-1_weight_{selected_weight}_page1.jpg"
    if os.path.exists(path_acc):
        display_image_autoscaled(path_acc, caption="Accident Scenario")
    else:
        st.warning("Image not found.")
    if not data_acc.empty:
        st.dataframe(data_acc[cols_to_display].transpose())
