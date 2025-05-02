import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from PIL import Image

# --- App config ---
st.set_page_config(layout="centered", page_title="Smart Charging Explorer")

st.title("Smart Charging Trade-off Explorer")

# --- Load experiment data ---
power_data = pd.read_csv("overall_power_side_results.csv")

# Convert to numeric
for col in ['energy_cost_all', 'total_energy_delivered', 'proportion_delivered']:
    power_data[col] = pd.to_numeric(power_data[col], errors='coerce')

# Filter static mix
power_data = power_data[power_data["CUTOFF_TIME_FOR_RESULTS_MIXING"] == -1].copy()

# Compute cost per kWh
power_data["cost_per_kWh"] = power_data["energy_cost_all"] / (power_data["total_energy_delivered"] + 1e-8)
power_data["rounded_weight"] = power_data["weight_obj_cost"].round().astype(int)

# Predefined weights
valid_weights = [1, 2, 3, 4, 10, 15, 20, 25, 30, 35, 50, 60, 70, 80, 100, 120, 150, 160,
                 170, 175, 180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235,
                 240, 245, 250, 255, 260, 265, 270, 275, 280, 285, 290, 295, 350, 450,
                 700, 1000, 10000]
exp_labels = [f"{w:.0e}" for w in valid_weights]
label_to_weight = dict(zip(exp_labels, valid_weights))

# --- User selection ---
st.subheader("Select a Weight Value")
selected_label = st.select_slider("Weight (Objective: Cost)", options=exp_labels, value=f"{100:.0e}")
matched_weight = label_to_weight[selected_label]

# --- Plot Pareto front ---
fig, ax = plt.subplots(figsize=(2.5, 1.5), dpi=100)
for scenario, group in power_data.groupby("Traffic-scenario"):
    color = 'C0' if scenario == "no-accident" else 'C1'
    marker = 'o' if scenario == "no-accident" else 'x'
    alpha = 0.3
    ax.scatter(group["cost_per_kWh"], group["proportion_delivered"], alpha=alpha, color=color, marker=marker)

    group_sorted = group.sort_values("cost_per_kWh")
    pareto = []
    max_y = -float('inf')
    for _, row in group_sorted.iterrows():
        if row['proportion_delivered'] > max_y:
            pareto.append(row)
            max_y = row['proportion_delivered']
    pareto_df = pd.DataFrame(pareto)
    ax.plot(pareto_df["cost_per_kWh"], pareto_df["proportion_delivered"], linewidth=1.5, color=color)

highlight_point = power_data[(power_data["Traffic-scenario"] == "no-accident") & (power_data["rounded_weight"] == matched_weight)]
if not highlight_point.empty:
    ax.scatter(highlight_point["cost_per_kWh"], highlight_point["proportion_delivered"],
               color="black", edgecolor="white", s=80, zorder=5)

ax.set_xlabel("TOU Cost ($/kWh)", fontsize=7)
ax.set_ylabel("Energy Met (%)", fontsize=7)
ax.tick_params(axis='both', labelsize=6)
ax.set_xlim(0, 0.15)
ax.set_ylim(65, 105)
ax.grid(True, alpha=0.2)
st.pyplot(fig)

# --- Get scenario data ---
cols = ["Traffic-scenario", "Transformer-capacity", "Scenario", "weight_obj_cost",
        "proportion_delivered", "total_energy_delivered", "total_energy_requested",
        "demands_fully_met", "energy_cost_all"]

data_acc = power_data[(power_data["Traffic-scenario"] == "45-mins-accident-1-capacity-remaining-start-10am") &
                      (power_data["rounded_weight"] == matched_weight)]
data_nacc = power_data[(power_data["Traffic-scenario"] == "no-accident") &
                       (power_data["rounded_weight"] == matched_weight)]

# --- Display scenario comparison ---
st.subheader("Scenario Comparison")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**No-Accident**")
    img_path = f"images/jpg_output/d_-1_no-accidentOffline-cap-1300-runnum-1_weight_{matched_weight}_page1.jpg"
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True)
    else:
        st.warning("Image not found.")
    if not data_nacc.empty:
        st.dataframe(data_nacc[cols].transpose(), use_container_width=True)

with col2:
    st.markdown("**Accident**")
    img_path = f"images/jpg_output/d_-1_45-mins-accident-1-capacity-remaining-start-10amOffline-cap-1300-runnum-1_weight_{matched_weight}_page1.jpg"
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True)
    else:
        st.warning("Image not found.")
    if not data_acc.empty:
        st.dataframe(data_acc[cols].transpose(), use_container_width=True)
