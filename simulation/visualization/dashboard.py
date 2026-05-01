#!/usr/bin/env python3
"""
Interactive Dashboard for Global Tourism Simulation.
Streamlit-based visualization with real-time controls.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import time
from pathlib import Path
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulation.simulation import Simulation
from simulation.data.loaders import load_country_data
from simulation.events.planned_events import create_fifa_world_cup_2026


# Page configuration
st.set_page_config(
    page_title="Global Tourism Simulation",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better layout
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .stTabs {
        margin-top: 20px;
    }
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize Streamlit session state."""
    if "simulation" not in st.session_state:
        st.session_state.simulation = None
        logger.info("Initialized simulation state: None")
    if "running" not in st.session_state:
        st.session_state.running = False
        logger.info("Initialized running state: False")
    if "speed" not in st.session_state:
        st.session_state.speed = 1.0
    if "tick" not in st.session_state:
        st.session_state.tick = 0
    if "selected_country" not in st.session_state:
        st.session_state.selected_country = None
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent = None


def create_simulation():
    """Create and initialize simulation."""
    with st.spinner("Initializing simulation..."):
        countries = load_country_data()

        config = {
            "agent_count": 4000,
            "segment_shares": {
                "budget": 0.30,
                "luxury": 0.20,
                "adventure": 0.25,
                "family": 0.25,
            },
            "choice_set_size": 50,
            "start_date": "2026-01-01",
            "duration_days": 365,
            "seed": 42,
        }

        sim = Simulation(config=config, countries_data=countries)
        sim.initialize()

        # Add FIFA World Cup 2026 as example planned event
        sim.planned_events.add_event(create_fifa_world_cup_2026())

        st.session_state.simulation = sim
        st.session_state.tick = 0

        logger.info(
            f"Simulation initialized: {len(sim.agents)} agents, {len(sim.destinations)} destinations"
        )
        return sim


def get_destination_data(sim):
    """Extract destination data for visualization."""
    data = []

    for code, dest in sim.destinations.items():
        visitors = dest.get_current_visitors()
        capacity_util = dest.get_crowding_ratio()
        crowding_level, crowding_color = dest.get_crowding_level()

        data.append(
            {
                "country_code": code,
                "country_name": dest.country_name,
                "visitors": visitors,
                "capacity": dest.base_capacity,
                "capacity_util": capacity_util,
                "crowding_level": crowding_level,
                "crowding_color": crowding_color,
                "tfi": dest.tfi,
                "attractiveness": dest.attractiveness,
                "latitude": dest.latitude,
                "longitude": dest.longitude,
            }
        )

    return pd.DataFrame(data)


def get_agent_sample_data(sim):
    """Extract sampled agent data for map visualization."""
    data = []

    segment_colors = {
        "budget": "#1f77b4",
        "luxury": "#ff7f0e",
        "adventure": "#2ca02c",
        "family": "#d62728",
    }

    for agent in sim.agents:
        if agent.agent_id in sim.sampled_agent_ids:
            if agent.state == "TRAVELING" and agent.current_destination:
                dest = sim.destinations.get(agent.current_destination)
                if dest:
                    data.append(
                        {
                            "agent_id": agent.agent_id,
                            "segment": agent.segment,
                            "home_country": agent.home_country,
                            "current_destination": agent.current_destination,
                            "days_remaining": agent.days_remaining,
                            "latitude": dest.latitude,
                            "longitude": dest.longitude,
                            "color": segment_colors.get(agent.segment, "#999999"),
                        }
                    )

    return pd.DataFrame(data)


def render_map(sim):
    """Render interactive world map."""
    dest_data = get_destination_data(sim)
    agent_data = get_agent_sample_data(sim)

    # Create choropleth base
    fig = px.choropleth(
        dest_data,
        locations="country_code",
        color="capacity_util",
        color_continuous_scale="RdYlGn_r",  # Red (high) to Green (low)
        range_color=(0, 1.5),
        title="Destination Crowding (Color = Capacity Utilization)",
        hover_name="country_name",
        hover_data={
            "country_code": True,
            "visitors": True,
            "capacity": True,
            "capacity_util": ":.1%",
            "tfi": ":.2f",
            "latitude": False,
            "longitude": False,
        },
    )

    # Add agent sample as scatter overlay
    if len(agent_data) > 0:
        fig.add_trace(
            go.Scattergeo(
                lon=agent_data["longitude"],
                lat=agent_data["latitude"],
                mode="markers",
                marker=dict(
                    size=6,
                    color=agent_data["color"],
                    symbol="circle",
                    line=dict(width=1, color="white"),
                ),
                text=agent_data.apply(
                    lambda row: (
                        f"Agent: {row['agent_id']}<br>"
                        f"Segment: {row['segment']}<br>"
                        f"Destination: {row['current_destination']}<br>"
                        f"Days Remaining: {row['days_remaining']}"
                    ),
                    axis=1,
                ),
                hoverinfo="text",
                name="Sampled Agents",
            )
        )

    fig.update_layout(
        height=600,
        margin=dict(l=0, r=0, t=50, b=0),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type="equirectangular",
        ),
        coloraxis_colorbar=dict(
            title="Capacity Util",
            tickformat=".0%",
        ),
    )

    return fig


def render_summary_metrics(sim):
    """Render summary metric cards."""
    data_summary = sim.data_collector.get_summary()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Simulation Day", value=f"Day {sim.tick}", delta=None)

    with col2:
        st.metric(
            label="Active Travelers", value=data_summary["active_travelers"], delta=None
        )

    with col3:
        st.metric(
            label="Total Trips (Recorded)",
            value=data_summary["total_trips_recorded"],
            delta=None,
        )

    with col4:
        st.metric(
            label="Sampled Agents", value=data_summary["sampled_agents"], delta=None
        )


def render_time_series(sim):
    """Render time series chart of arrivals."""
    arrivals = sim.data_collector.global_arrivals

    if len(arrivals) < 2:
        st.info("Run simulation for at least 2 ticks to see time series data.")
        return

    df = pd.DataFrame(
        {
            "Day": range(1, len(arrivals) + 1),
            "Arrivals": arrivals,
        }
    )

    fig = px.line(
        df,
        x="Day",
        y="Arrivals",
        title="Daily Arrivals Over Time",
        markers=False,
    )

    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="Simulation Day",
        yaxis_title="Number of Arrivals",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_top_destinations(sim):
    """Render top 10 destinations bar chart."""
    dest_data = get_destination_data(sim)

    if len(dest_data) == 0:
        return

    # Sort by current visitors
    top_10 = dest_data.nlargest(10, "visitors")[
        ["country_name", "visitors", "capacity_util"]
    ]

    fig = px.bar(
        top_10,
        x="visitors",
        y="country_name",
        orientation="h",
        title="Top 10 Destinations by Current Visitors",
        color="capacity_util",
        color_continuous_scale="RdYlGn_r",
    )

    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="Current Visitors",
        yaxis_title="Country",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_segment_breakdown(sim):
    """Render segment breakdown pie chart."""
    # Count active travelers by segment
    segment_counts = {}
    for agent in sim.agents:
        if agent.state == "TRAVELING":
            segment_counts[agent.segment] = segment_counts.get(agent.segment, 0) + 1

    if not segment_counts:
        st.info("No active travelers yet.")
        return

    df = pd.DataFrame(
        {
            "Segment": list(segment_counts.keys()),
            "Count": list(segment_counts.values()),
        }
    )

    fig = px.pie(
        df,
        names="Segment",
        values="Count",
        title="Active Travelers by Segment",
        color="Segment",
        color_discrete_map={
            "budget": "#1f77b4",
            "luxury": "#ff7f0e",
            "adventure": "#2ca02c",
            "family": "#d62728",
        },
    )

    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_destination_details(sim, country_code):
    """Render detailed destination information panel."""
    if country_code not in sim.destinations:
        st.error(f"Country {country_code} not found.")
        return

    dest = sim.destinations[country_code]
    dest_dict = dest.to_dict()

    st.subheader(f"📍 {dest.country_name}")

    # Key metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Current Visitors", value=dest_dict["current_visitors"], delta=None
        )

    with col2:
        st.metric(
            label="Capacity Utilization",
            value=f"{dest_dict['crowding_ratio']:.1%}",
            delta=f"{dest_dict['crowding_level']} ({dest_dict['crowding_color']})",
        )

    with col3:
        st.metric(
            label="Tourism Friendliness (TFI)",
            value=f"{dest_dict['tfi']:.2f}",
            delta="↑ Improving"
            if dest_dict["tfi_trend"] == "stable"
            else "↓ Declining",
        )

    # Additional details
    with st.expander("Detailed Information", expanded=False):
        st.write(f"**Country Code**: {dest_dict['country_code']}")
        st.write(f"**Base Capacity**: {dest_dict['base_capacity']:,}")
        st.write(f"**Effective Capacity**: {dest_dict['effective_capacity']:,}")
        st.write(f"**Attractiveness Score**: {dest_dict['attractiveness']:.2f}")
        st.write(f"**Cost Index**: {dest_dict['cost_index']:.1f}")
        st.write(f"**Risk Score**: {dest_dict['risk_score']:.2f}")
        st.write(f"**Climate Zone**: {dest_dict['climate_zone']}")

    # Policy suggestions
    suggestions = dest.get_rectification_suggestions()
    if suggestions:
        st.warning("⚠️ **Rectification Suggestions**:")
        for suggestion in suggestions:
            st.write(f"- {suggestion}")

    # Visitor origins (placeholder - would need origin tracking)
    st.info("📊 Visitor origins chart - Coming in next iteration")


def main():
    """Main dashboard application."""
    st.title("🌍 Global Tourism Simulation")
    st.markdown("**Agent-based simulation of global tourism dynamics**")

    # Initialize session state
    init_session_state()

    # Callback functions for buttons
    def toggle_running():
        st.session_state.running = not st.session_state.running
        logger.info(f"Toggled running state: {st.session_state.running}")

    def confirm_stop():
        """Mark that stop is confirmed for next click"""
        st.session_state.stop_confirm = True
        logger.info("Stop confirmation set")

    def stop_simulation():
        if st.session_state.get("stop_confirm", False):
            st.session_state.running = False
            st.session_state.simulation = None
            st.session_state.tick = 0
            st.session_state.stop_confirm = False
            logger.info("Simulation stopped and reset")
        else:
            st.session_state.stop_confirm = True
            logger.info("Stop confirmation pending")

    def trigger_disaster():
        import random

        countries = list(st.session_state.simulation.destinations.keys())
        target = random.choice(countries)
        st.session_state.simulation.unplanned_events.trigger_event(
            country_code=target,
            event_type="disaster",
            severity=0.7,
            current_date=st.session_state.simulation.current_date,
            name=f"Natural Disaster in {target}",
        )
        logger.info(f"Disaster triggered in {target}")
        st.success(f"Disaster triggered in {target}!")

    def trigger_epidemic():
        import random

        countries = list(st.session_state.simulation.destinations.keys())
        target = random.choice(countries)
        st.session_state.simulation.unplanned_events.trigger_event(
            country_code=target,
            event_type="epidemic",
            severity=0.6,
            current_date=st.session_state.simulation.current_date,
        )
        logger.info(f"Epidemic triggered in {target}")
        st.success(f"Epidemic triggered in {target}!")

    def step_simulation(sim_obj):
        """Advance simulation by one day"""
        sim_obj.step()
        st.session_state.tick += 1
        logger.info(f"Manual step: tick {st.session_state.tick}")

    def save_scenario():
        st.info("Scenario save - Coming in next iteration")
        logger.info("Save scenario clicked (not implemented)")

    # Sidebar: Controls
    with st.sidebar:
        st.header("🎮 Controls")

        # Simulation initialization
        if st.session_state.simulation is None:
            if st.button(
                "Initialize Simulation",
                type="primary",
                use_container_width=True,
                on_click=lambda: logger.info("Initialize button clicked"),
            ):
                create_simulation()
                st.rerun()
        else:
            # Control buttons row 1
            col1, col2 = st.columns(2)
            with col1:
                st.button(
                    "▶️ Run" if not st.session_state.running else "⏸️ Pause",
                    use_container_width=True,
                    on_click=toggle_running,
                    key="run_pause_button",
                )
            with col2:
                # Stop button with confirmation
                stop_label = (
                    "⏹️ Stop"
                    if not st.session_state.get("stop_confirm", False)
                    else "⚠️ Confirm Stop"
                )
                st.button(
                    stop_label,
                    use_container_width=True,
                    on_click=confirm_stop
                    if not st.session_state.get("stop_confirm", False)
                    else stop_simulation,
                    type="primary"
                    if st.session_state.get("stop_confirm", False)
                    else "secondary",
                    key="stop_button",
                )

            # Control buttons row 2: Step button
            st.button(
                "⏭️ Step (1 day)",
                use_container_width=True,
                on_click=lambda: step_simulation(sim),
                disabled=st.session_state.running,
            )

            # Speed control
            speed = st.select_slider(
                "Simulation Speed",
                options=[0.5, 1.0, 2.0, 4.0],
                value=st.session_state.speed,
                key="speed_slider",
            )
            st.session_state.speed = speed

            # Trigger event button
            st.divider()
            st.subheader("⚡ Trigger Event")

            st.button(
                "🌋 Natural Disaster",
                use_container_width=True,
                on_click=trigger_disaster,
            )

            st.button(
                "🦠 Epidemic Outbreak",
                use_container_width=True,
                on_click=trigger_epidemic,
            )

            # Scenario save/load
            st.divider()
            st.subheader("💾 Scenario")

            st.button(
                "Save Configuration", use_container_width=True, on_click=save_scenario
            )

    # Main content area
    if st.session_state.simulation is None:
        # Welcome screen
        st.info("👈 Click **'Initialize Simulation'** in the sidebar to begin.")

        st.markdown("""
        ### Features:
        - **4,000 tourist agents** with segment-specific behavior
        - **177 countries** with capacity constraints and TFI dynamics
        - **Planned events** (e.g., FIFA World Cup)
        - **Unplanned events** (disasters, epidemics)
        - **Real-time visualization** of tourism flows
        
        ### How to Use:
        1. Initialize the simulation
        2. Click **Run** to start
        3. Watch agents travel between countries
        4. Click on countries to see details
        5. Trigger events to see impacts
        """)

        return

    sim = st.session_state.simulation

    # Run simulation step if active
    if st.session_state.running:
        # Control frame rate based on speed (base: 10 FPS at 1× speed)
        frame_time = 0.1 / st.session_state.speed
        time.sleep(frame_time)

        # Run single step
        sim.step()
        st.session_state.tick += 1

        # Log progress every 100 ticks
        if st.session_state.tick % 100 == 0:
            logger.info(
                f"Simulation tick: {st.session_state.tick}, active travelers: {sim.data_collector.get_summary()['active_travelers']}"
            )

        # Force rerun to continue simulation
        st.rerun()

    # Render dashboard
    render_summary_metrics(sim)

    st.divider()

    # Main layout: Map (left) + Charts (right)
    col_map, col_charts = st.columns([6, 4])

    with col_map:
        # Interactive map
        fig_map = render_map(sim)
        st.plotly_chart(fig_map, use_container_width=True, key="map")

        # Click handler (using session state)
        st.info(
            "💡 **Tip**: Click on a country in the map to see details (feature coming soon)"
        )

    with col_charts:
        # Time series
        render_time_series(sim)

        # Top destinations
        render_top_destinations(sim)

        # Segment breakdown
        render_segment_breakdown(sim)

    # Country details panel (if selected)
    if st.session_state.selected_country:
        st.divider()
        render_destination_details(sim, st.session_state.selected_country)


if __name__ == "__main__":
    main()
