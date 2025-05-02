import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from PIL import Image

# --- App config ---
st.set_page_config(layout="wide")
st.title("Smart Charging Trade-off Explorer")

# --- Load experiment data ---
power_data = pd.read_csv("overall_power_side_results.csv")

# Convert to numeric to ensure proper math
to_numeric_cols = ['energy_cost_all', 'total_energy_delivered', 'proportion_delivered']
for col in to_numeric_cols:
    power_data[col] = pd.to_numeric(power_data[col], errors='coerce')

# Filter only static mix scenarios
power_data = power_data[power_data["CUTOFF_TIME_FOR_RESULTS_MIXING"] == -1].copy()

# Compute cost per kWh using total energy delivered
power_data["cost_per_kWh"] = power_data["energy_cost_all"] / (power_data["total_energy_delivered"] + 1e-8)

# Round weights for slider and image matching
power_data["rounded_weight"] = power_data["weight_obj_cost"].round().astype(int)
unique_weights = sorted(power_data["rounded_weight"].unique())

# --- User selection from pre-defined slider ---
st.subheader("Select a Weight Value")
matched_weight = st.slider("Weight (Objective: Cost)", min_value=min(unique_weights), max_value=max(unique_weights), step=1, value=100, format="%d")

# --- Plotting ---
st.subheader("Pareto Front (All Scenarios)")
fig, ax = plt.subplots(figsize=(6, 4))

for scenario, group in power_data.groupby("Traffic-scenario"):
    color = 'C0' if scenario == "no-accident" else 'C1'
    marker = 'o' if scenario == "no-accident" else 'x'
    alpha = 0.3
    ax.scatter(group["cost_per_kWh"], group["proportion_delivered"], label=f"{scenario} (all)", alpha=alpha, color=color, marker=marker)

    # Draw Pareto front
    group_sorted = group.sort_values("cost_per_kWh")
    pareto = []
    max_y = -float('inf')
    for _, row in group_sorted.iterrows():
        if row['proportion_delivered'] > max_y:
            pareto.append(row)
            max_y = row['proportion_delivered']
    pareto_df = pd.DataFrame(pareto)
    ax.plot(pareto_df["cost_per_kWh"], pareto_df["proportion_delivered"], label=f"{scenario} (Pareto)", linewidth=2, color=color)

# Highlight selected weight's point from no-accident
highlight_point = power_data[(power_data["Traffic-scenario"] == "no-accident") & (power_data["rounded_weight"] == matched_weight)]
if not highlight_point.empty:
    ax.scatter(highlight_point["cost_per_kWh"], highlight_point["proportion_delivered"], color="black", edgecolor="white", s=100, label="Selected", zorder=5)

ax.set_xlabel("Mean TOU Cost ($/kWh)")
ax.set_ylabel("Energy demand met (%)")
ax.set_xlim(0, 0.15)
ax.set_ylim(65, 105)
ax.grid(True, alpha=0.2)
ax.legend(fontsize=8, loc="lower center")
st.pyplot(fig)

# --- Get both scenarios with matched weight ---
data_acc = power_data[(power_data["Traffic-scenario"] == "45-mins-accident-1-capacity-remaining-start-10am") & (power_data["rounded_weight"] == matched_weight)]
data_nacc = power_data[(power_data["Traffic-scenario"] == "no-accident") & (power_data["rounded_weight"] == matched_weight)]

# Columns to show only
cols_to_display = [
    "Traffic-scenario", "Transformer-capacity", "Scenario", "Algorithm", "Run_number",
    "weight_obj_cost", "proportion_delivered", "demands_fully_met", "peak_current",
    "demand_charge", "energy_cost_all", "total_energy_delivered",
    "total_energy_requested", "aggregate_power_total"
]

col1, col2 = st.columns(2)

with col1:
    st.markdown("**No-Accident Scenario**")
    image_path = f"images/combined_plot_1300kW_weight_{matched_weight}.png"
    st.markdown(f"_Image path: `{image_path}`_")
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.warning("Image not found.")
    if not data_nacc.empty:
        st.dataframe(data_nacc[cols_to_display].transpose())

with col2:
    st.markdown("**Accident Scenario**")
    st.markdown(f"_Image path: `{image_path}`_")
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.warning("Image not found.")
    if not data_acc.empty:
        st.dataframe(data_acc[cols_to_display].transpose())
