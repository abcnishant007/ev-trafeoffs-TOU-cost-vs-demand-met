import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from PIL import Image
from base64 import b64encode

# --- App config ---
st.set_page_config(layout="wide")
st.title("Smart Charging Trade-off Explorer")

# --- Load experiment data ---
power_data = pd.read_csv("overall_power_side_results.csv")

# Convert to numeric
to_numeric_cols = ['energy_cost_all', 'total_energy_delivered', 'proportion_delivered']
for col in to_numeric_cols:
    power_data[col] = pd.to_numeric(power_data[col], errors='coerce')

# Filter only static mix scenarios
power_data = power_data[power_data["CUTOFF_TIME_FOR_RESULTS_MIXING"] == -1].copy()

# Compute cost per kWh using total energy delivered
power_data["cost_per_kWh"] = power_data["energy_cost_all"] / (power_data["total_energy_delivered"] + 1e-8)
power_data["rounded_weight"] = power_data["weight_obj_cost"].round().astype(int)

# --- Predefined valid weights only ---
valid_weights = [1, 2, 3, 4, 10, 15, 20, 25, 30, 35, 50, 60, 70, 80, 100, 120, 150, 160,
                 170, 175, 180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235,
                 240, 245, 250, 255, 260, 265, 270, 275, 280, 285, 290, 295, 350, 450,
                 700, 1000, 10000]
exp_labels = [f"{w:.0e}" for w in valid_weights]
label_to_weight = dict(zip(exp_labels, valid_weights))

# --- User selection from slider ---
st.subheader("Select a Weight Value for TOU cost (Total energy is set to 30)")
selected_label = st.select_slider("Weight (Objective: Cost)", options=exp_labels, value=f"{100:.0e}")
matched_weight = label_to_weight[selected_label]

# --- Pareto Front Plot ---
st.subheader("Pareto Front (All Scenarios)")
fig, ax = plt.subplots(figsize=(4.8, 2.8), dpi=300)

for scenario, group in power_data.groupby("Traffic-scenario"):
    color = 'C0' if scenario == "no-accident" else 'C1'
    marker = 'o' if scenario == "no-accident" else 'x'
    ax.scatter(group["cost_per_kWh"], group["proportion_delivered"],
               label=f"{scenario} (all)", alpha=0.3, color=color, marker=marker)

    # Pareto front
    group_sorted = group.sort_values("cost_per_kWh")
    pareto = []
    max_y = -float('inf')
    for _, row in group_sorted.iterrows():
        if row['proportion_delivered'] > max_y:
            pareto.append(row)
            max_y = row['proportion_delivered']
    pareto_df = pd.DataFrame(pareto)
    ax.plot(pareto_df["cost_per_kWh"], pareto_df["proportion_delivered"],
            label=f"{scenario} (Pareto)", linewidth=2, color=color)

# Highlight selected point
highlight_point = power_data[(power_data["Traffic-scenario"] == "no-accident") &
                             (power_data["rounded_weight"] == matched_weight)]
if not highlight_point.empty:
    ax.scatter(highlight_point["cost_per_kWh"], highlight_point["proportion_delivered"],
               color="black", edgecolor="white", s=100, label="Selected", zorder=5)

ax.set_xlabel("Mean TOU Cost ($/kWh)", fontsize=6)
ax.set_ylabel("Energy demand met (%)", fontsize=6)
ax.tick_params(axis='both', labelsize=6)
ax.set_xlim(0, 0.15)
ax.set_ylim(65, 105)
ax.grid(True, alpha=0.2)
ax.legend(fontsize=4, loc="lower center")
st.pyplot(fig)

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
                      (power_data["rounded_weight"] == matched_weight)]
data_nacc = power_data[(power_data["Traffic-scenario"] == "no-accident") &
                       (power_data["rounded_weight"] == matched_weight)]

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
    img_path = f"images/jpg_output/d_-1_no-accidentOffline-cap-1300-runnum-1_weight_{matched_weight}_page1.jpg"
    if os.path.exists(img_path):
        display_image_autoscaled(img_path, caption="No-Accident Scenario")
    else:
        st.warning("Image not found.")
    if not data_nacc.empty:
        st.dataframe(data_nacc[cols_to_display].transpose())

with col2:
    st.markdown("**Accident Scenario**")
    img_path = f"images/jpg_output/d_-1_45-mins-accident-1-capacity-remaining-start-10amOffline-cap-1300-runnum-1_weight_{matched_weight}_page1.jpg"
    if os.path.exists(img_path):
        display_image_autoscaled(img_path, caption="Accident Scenario")
    else:
        st.warning("Image not found.")
    if not data_acc.empty:
        st.dataframe(data_acc[cols_to_display].transpose())
