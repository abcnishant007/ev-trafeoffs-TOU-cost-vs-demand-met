import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

# --- Title and Intro ---
st.set_page_config(layout="wide")
st.title("Interactive Exploration of Smart Charging Trade-offs")
st.markdown("""
This tool visualizes the trade-off between minimizing **TOU cost** and maximizing **total energy demand met** 
for a range of optimization weightings. Each point represents a smart-charging solution.

Use the sidebar to choose a scenario or select a point from the scatter plot to view the corresponding solution image.
""")

# --- Sidebar: Scenario selection (placeholder for future expansion) ---
with st.sidebar:
    st.header("Scenario Selector")
    selected_scenario = st.selectbox("Scenario", ["45-mins-accident-1-start-10am"], index=0)

# --- Load and plot Pareto front data (placeholder example) ---
st.subheader("Pareto Front: Cost vs. Energy Demand Met")

# Fake data for illustration (replace with actual)
weights = [1,2,3,4,10,15,20,25,30,35,50,60,70,80,100,120,150,160] + list(range(170, 300, 5)) + [350,450,700,1000,10000]
costs = [0.12 - 0.00001*w if w < 1000 else 0.04 for w in weights]  # synthetic TOU cost
energy_met = [70 + 0.02*w if w < 1000 else 98 for w in weights]     # synthetic energy demand met

pareto_df = pd.DataFrame({"Weight": weights, "Cost": costs, "EnergyMet": energy_met})

fig, ax = plt.subplots()
scatter = ax.scatter(pareto_df["Cost"], pareto_df["EnergyMet"], picker=True, c="blue")
ax.set_xlabel("Mean TOU Cost ($/kWh)")
ax.set_ylabel("Energy Demand Met (%)")
st.pyplot(fig)

# --- User click handling ---
st.subheader("Selected Solution")
clicked_index = st.number_input("Enter index of point (temporary until click enabled):", min_value=0, max_value=len(pareto_df)-1, value=0)
selected_weight = pareto_df.iloc[clicked_index]["Weight"]
st.markdown(f"**Selected Weight:** {selected_weight}")

# --- Display corresponding image (placeholder) ---
# You can later map weights to image filenames, e.g., weight_30.png, etc.
image_path = f"images/solution_weight_{int(selected_weight)}.png"  # replace with actual

try:
    img = Image.open(image_path)
    st.image(img, caption=f"Smart-charging solution for weight = {int(selected_weight)}")
except FileNotFoundError:
    st.warning(f"No image found for weight = {int(selected_weight)}. Please upload the corresponding image.")
