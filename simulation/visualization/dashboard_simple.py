#!/usr/bin/env python3
"""
Simple Dashboard for Global Tourism Simulation.
Minimal Streamlit app with working controls.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulation.simulation import Simulation
from simulation.data.loaders import load_country_data


st.set_page_config(page_title="Tourism Simulation", layout="wide")

# Initialize session state
if "sim" not in st.session_state:
    st.session_state.sim = None
if "running" not in st.session_state:
    st.session_state.running = False
if "tick" not in st.session_state:
    st.session_state.tick = 0


# Callback functions
def toggle_running():
    st.session_state.running = not st.session_state.running


def reset_sim():
    st.session_state.sim = None
    st.session_state.running = False
    st.session_state.tick = 0


def trigger_disaster():
    import random

    sim = st.session_state.sim
    countries = list(sim.destinations.keys())
    target = random.choice(countries)
    sim.unplanned_events.trigger_event(
        country_code=target,
        event_type="disaster",
        severity=0.7,
        current_date=sim.current_date,
    )
    st.success(f"Disaster in {target}")


def trigger_epidemic():
    import random

    sim = st.session_state.sim
    countries = list(sim.destinations.keys())
    target = random.choice(countries)
    sim.unplanned_events.trigger_event(
        country_code=target,
        event_type="epidemic",
        severity=0.6,
        current_date=sim.current_date,
    )
    st.success(f"Epidemic in {target}")


# Sidebar
with st.sidebar:
    st.header("Controls")

    if st.session_state.sim is None:
        if st.button(
            "Initialize",
            type="primary",
            use_container_width=True,
            on_click=lambda: None,
        ):
            countries = load_country_data()
            sim = Simulation(countries_data=countries)
            sim.initialize()
            st.session_state.sim = sim
            st.session_state.tick = 0
            st.rerun()
    else:
        sim = st.session_state.sim

        col1, col2 = st.columns(2)
        with col1:
            st.button(
                "▶️ Run" if not st.session_state.running else "⏸️",
                use_container_width=True,
                on_click=toggle_running,
            )

        with col2:
            st.button("⏹️ Reset", use_container_width=True, on_click=reset_sim)

        # Speed
        speed = st.select_slider(
            "Speed",
            options=[0.5, 1.0, 2.0, 4.0],
            value=st.session_state.get("speed", 1.0),
        )
        st.session_state.speed = speed

        st.divider()

        # Events
        st.button("🌋 Disaster", use_container_width=True, on_click=trigger_disaster)
        st.button("🦠 Epidemic", use_container_width=True, on_click=trigger_epidemic)

# Main content
if st.session_state.sim is None:
    st.title("🌍 Global Tourism Simulation")
    st.info("Click **Initialize** in the sidebar to start")
else:
    sim = st.session_state.sim

    # Run simulation if active
    if st.session_state.running:
        frame_time = 0.1 / st.session_state.speed
        time.sleep(frame_time)
        sim.step()
        st.session_state.tick += 1
        st.rerun()

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Day", st.session_state.tick)
    with col2:
        st.metric(
            "Active Travelers", sim.data_collector.get_summary()["active_travelers"]
        )
    with col3:
        st.metric(
            "Total Trips", sim.data_collector.get_summary()["total_trips_recorded"]
        )
    with col4:
        st.metric("Destinations", len(sim.destinations))

    st.divider()

    # Map
    st.subheader("Destination Crowding")
    map_data = []
    for code, dest in sim.destinations.items():
        map_data.append(
            {
                "country_code": code,
                "country_name": dest.country_name,
                "visitors": dest.get_current_visitors(),
                "capacity_util": dest.get_crowding_ratio(),
                "lat": dest.latitude,
                "lon": dest.longitude,
            }
        )

    if map_data:
        map_df = pd.DataFrame(map_data)
        fig = px.choropleth(
            map_df,
            locations="country_code",
            color="capacity_util",
            color_continuous_scale="RdYlGn_r",
            range_color=(0, 1.5),
            hover_name="country_name",
            hover_data={"visitors": True, "capacity_util": ":.1%"},
            title="Capacity Utilization (Red = High Crowding)",
        )
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Arrivals Over Time")
        arrivals = sim.data_collector.global_arrivals
        if len(arrivals) > 0:
            df = pd.DataFrame({"Day": range(len(arrivals)), "Arrivals": arrivals})
            st.line_chart(df, x="Day", y="Arrivals")
        else:
            st.info("No data yet")

    with col2:
        st.subheader("Top Destinations")
        dest_data = []
        for code, dest in sim.destinations.items():
            dest_data.append(
                {
                    "Country": dest.country_name,
                    "Visitors": dest.get_current_visitors(),
                    "Capacity Util": dest.get_crowding_ratio(),
                }
            )
        if dest_data:
            df = pd.DataFrame(dest_data)
            top10 = df.nlargest(10, "Visitors")
            st.bar_chart(top10.set_index("Country")["Visitors"])
