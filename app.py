import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from PIL import Image

# --- App config ---
st.set_page_config(layout="wide")
st.title("Smart Charging Trade-off Explorer")

# --- Load experiment data ---
data = pd.read_csv("data.csv")

# Load total energy delivered for each scenario
power_data = pd.read_csv("overall_power_side_results.csv")
total_energy_delivered = power_data[["Traffic-scenario", "weight_obj_cost", "energy_delivered"]]

# Merge to get correct denominator for cost/kWh
merged_data = pd.merge(data, total_energy_delivered, on=["Traffic-scenario", "weight_obj_cost"], how="left")

# Compute cost per kWh using energy delivered (not proportion)
merged_data["cost_per_kWh"] = merged_data["energy_cost_all"] / merged_data["energy_delivered"]

# Round weights for image matching
merged_data["rounded_weight"] = merged_data["weight_obj_cost"].round().astype(int)

# --- Sidebar ---
st.sidebar.header("Filter Options")
scenario_options = merged_data["Traffic-scenario"].unique()
selected_scenario = st.sidebar.selectbox("Select Traffic Scenario", scenario_options)

# Filter data for selected scenario
filtered_data = merged_data[merged_data["Traffic-scenario"] == selected_scenario]

# --- Plotting ---
st.subheader(f"Pareto Front: {selected_scenario}")
fig, ax = plt.subplots()
scatter = ax.scatter(filtered_data["cost_per_kWh"], filtered_data["proportion_delivered"], c=filtered_data["weight_obj_cost"], cmap="plasma", picker=True)
ax.set_xlabel("Cost per kWh")
ax.set_ylabel("Energy Delivered (%)")
plt.colorbar(scatter, label="Weight")
st.pyplot(fig)

# --- User selection from coordinates ---
st.subheader("Explore by Clicked Coordinates")
x_clicked = st.number_input("X: Cost per kWh", min_value=0.0, step=0.01, value=7.06)
y_clicked = st.number_input("Y: Energy Delivered (%)", min_value=0.0, max_value=100.0, step=0.1, value=100.0)

# Match closest point
filtered_data["distance"] = ((filtered_data["cost_per_kWh"] - x_clicked)**2 + (filtered_data["proportion_delivered"] - y_clicked)**2)**0.5
closest = filtered_data.sort_values("distance").iloc[0]
matched_weight = int(closest['weight_obj_cost'])

# --- Display match info ---
st.markdown(f"**Matched weight:** {matched_weight}, Delivered: {closest['proportion_delivered']:.2f}%, TOU cost: ${closest['energy_cost_all']:.2f}, Energy Delivered: {closest['energy_delivered']:.2f} kWh")

# --- Load and show both scenario images ---
image_folder = "images"
base_img_filename = f"combined_plot_1300kW_weight_{matched_weight}.pdf"
image_path_base = os.path.join(image_folder, base_img_filename)

scenario_acc = "45-mins-accident-1-capacity-remaining-start-10am"
scenario_nacc = "no-accident"

# --- Get matching data from both scenarios ---
data_acc = merged_data[(merged_data["Traffic-scenario"] == scenario_acc) & (merged_data["weight_obj_cost"] == matched_weight)]
data_nacc = merged_data[(merged_data["Traffic-scenario"] == scenario_nacc) & (merged_data["weight_obj_cost"] == matched_weight)]

col1, col2 = st.columns(2)

with col1:
    st.markdown("**No-Accident Scenario**")
    try:
        st.image(f"images/combined_plot_1300kW_weight_{matched_weight}.pdf", use_column_width=True)
    except:
        st.warning("Image not found.")
    if not data_nacc.empty:
        st.write(data_nacc.iloc[0])

with col2:
    st.markdown("**Accident Scenario**")
    try:
        st.image(f"images/combined_plot_1300kW_weight_{matched_weight}.pdf", use_column_width=True)
    except:
        st.warning("Image not found.")
    if not data_acc.empty:
        st.write(data_acc.iloc[0])
