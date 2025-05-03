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
power_data = power_data.reset_index(drop=True)

# --- Abbreviation note ---
st.markdown("""
> **Note:**  
> - **TOU** = *Time-of-Use energy cost weighting*  
> - **TED** = *Total Energy Delivered weighting*  
> - The ratio shown below is \\( \\frac{W_{\\text{TOU}}}{W_{\\text{TED}}} \\)
""")
# > - TED is fixed at 30.  

# --- Build Plot ---
st.subheader("Click on any point to view the corresponding charging profiles")

fig = go.Figure()

# Marker types and colors
marker_map = {
    "no-accident": ("circle", "#FFA500"),      # orange
    "45-mins-accident-1-capacity-remaining-start-10am": ("x", "#1f77b4"),  # tab:blue
}
grey_color = "rgba(120,120,120,0.3)"  # non-Pareto blobs

# Scatter blobs (non-Pareto)
for scenario, group in power_data.groupby("Traffic-scenario"):
    symbol, _ = marker_map.get(scenario, ("circle", grey_color))
    fig.add_trace(go.Scatter(
        x=group["cost_per_kWh"],
        y=group["proportion_delivered"],
        mode="markers",
        name=f"{scenario} (non-Pareto)",
        marker=dict(size=6, opacity=0.3, symbol=symbol, color=grey_color),
        hovertext=group["weight_obj_cost"].round(2).astype(str),
        hovertemplate="TOU/TED Weight: %{hovertext}<extra></extra>",
        showlegend=False
    ))

# Pareto curves and highlighted points
for scenario, group in power_data.groupby("Traffic-scenario"):
    symbol, color = marker_map.get(scenario, ("circle", "#000000"))
    group_sorted = group.sort_values("cost_per_kWh")
    pareto = []
    max_y = -float("inf")
    for _, row in group_sorted.iterrows():
        if row["proportion_delivered"] > max_y:
            pareto.append(row)
            max_y = row["proportion_delivered"]
    pareto_df = pd.DataFrame(pareto)

    # Pareto line
    fig.add_trace(go.Scatter(
        x=pareto_df["cost_per_kWh"],
        y=pareto_df["proportion_delivered"],
        mode="lines",
        name=f"{scenario} Pareto",
        line=dict(width=2, color=color),
        hoverinfo="skip"
    ))

    # Pareto points
    fig.add_trace(go.Scatter(
        x=pareto_df["cost_per_kWh"],
        y=pareto_df["proportion_delivered"],
        mode="markers",
        name=f"{scenario} Pareto Points",
        marker=dict(size=6, symbol=symbol, color=color),
        hovertext=pareto_df["weight_obj_cost"].round(2).astype(str),
        hovertemplate="TOU/TED Weight: %{hovertext}<extra></extra>",
        showlegend=False
    ))

fig.update_layout(
    xaxis=dict(title="TOU Cost ($/kWh)", range=[0, 0.15]),
    yaxis=dict(title="Energy Demand Met (%)", range=[65, 105]),
    height=360,
    width=1080, 
    legend=dict(font=dict(size=13)),
    # margin=dict(l=20, r=10, t=30, b=30)
)


# --- Initialize session state ---
if "selected_weight" not in st.session_state:
    st.session_state.selected_weight = 100

# --- Click interaction using pointIndex ---
clicked_points = plotly_events(fig, click_event=True, override_height=360)
if clicked_points and isinstance(clicked_points[0], dict):
    try:
        point_index = clicked_points[0].get("pointIndex")
        if point_index is not None:
            selected_row = power_data.iloc[point_index]
            st.session_state.selected_weight = int(round(float(selected_row["weight_obj_cost"])))
    except Exception as e:
        st.error(f"Error extracting clicked weight using pointIndex: {e}")

# --- Show selected ratio only ---
selected_weight = st.session_state.selected_weight
st.markdown(f"### 🔍 Selected TOU/TED Ratio: **{selected_weight / 30:.2f}**")

# --- Image display function ---
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

# --- Load matching rows ---
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

# --- Scenario Comparison UI ---
st.subheader("Scenario Comparison")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**No-Accident Scenario**")
    path = f"images/jpg_output/d_-1_no-accidentOffline-cap-1300-runnum-1_weight_{selected_weight}_page1.jpg"
    if os.path.exists(path):
        display_image_autoscaled(path, caption="No-Accident Scenario")
    else:
        st.warning("Image not found.")
    if not data_nacc.empty:
        st.dataframe(data_nacc[cols_to_display].astype(str).transpose())

with col2:
    st.markdown("**Accident Scenario**")
    path = f"images/jpg_output/d_-1_45-mins-accident-1-capacity-remaining-start-10amOffline-cap-1300-runnum-1_weight_{selected_weight}_page1.jpg"
    if os.path.exists(path):
        display_image_autoscaled(path, caption="Accident Scenario")
    else:
        st.warning("Image not found.")
    if not data_acc.empty:
        st.dataframe(data_acc[cols_to_display].astype(str).transpose())
