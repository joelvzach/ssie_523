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


def create_simulation(agent_count: int = 4000):
    """Create and initialize simulation with configured events.

    Args:
        agent_count: Number of tourist agents (default: 4000)
    """
    with st.spinner(f"Initializing simulation with {agent_count:,} agents..."):
        countries = load_country_data()

        config = {
            "agent_count": agent_count,
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

        # Add configured events from session state
        if "configured_events" in st.session_state:
            for event_config in st.session_state.configured_events:
                from simulation.events.planned_events import PlannedEvent

                event = PlannedEvent(
                    name=event_config["name"],
                    country_code=event_config["country"],
                    start_date=event_config["start"],
                    end_date=event_config["end"],
                    magnitude=event_config["magnitude"],
                    segment_appeal=event_config["appeal"],
                    expected_footfall=500000,  # Default value (removed from UI)
                    pre_event_days=30,  # Default value (removed from UI)
                )
                sim.planned_events.add_event(event)

            logger.info(
                f"Added {len(st.session_state.configured_events)} configured events"
            )

        st.session_state.simulation = sim
        st.session_state.tick = 0

        logger.info(
            f"Simulation initialized: {len(sim.agents):,} agents, {len(sim.destinations)} destinations"
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
    """Extract sampled agent data for map visualization (traveling agents)."""
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


def get_agent_home_data(sim):
    """Extract agent home country data for map visualization."""
    from collections import Counter

    # Count agents by home country
    home_counts = Counter()
    home_segments = {}

    for agent in sim.agents:
        if agent.agent_id in sim.sampled_agent_ids:
            home = agent.home_country
            home_counts[home] += 1

            # Track segment distribution
            if home not in home_segments:
                home_segments[home] = {
                    "budget": 0,
                    "luxury": 0,
                    "adventure": 0,
                    "family": 0,
                }
            home_segments[home][agent.segment] += 1

    # Convert to dataframe with coordinates
    data = []
    for country_code, count in home_counts.items():
        dest = sim.destinations.get(country_code)
        if dest:
            segments = home_segments[country_code]
            total = sum(segments.values())
            data.append(
                {
                    "country_code": country_code,
                    "country_name": dest.country_name,
                    "agent_count": count,
                    "latitude": dest.latitude,
                    "longitude": dest.longitude,
                    "tooltip": f"{dest.country_name}: {count} agents\n"
                    f"Budget: {segments['budget']} | Luxury: {segments['luxury']}\n"
                    f"Adventure: {segments['adventure']} | Family: {segments['family']}",
                }
            )

    return pd.DataFrame(data)


def render_map(sim):
    """Render interactive world map with dynamic color scaling."""
    dest_data = get_destination_data(sim)
    agent_data = get_agent_sample_data(sim)

    # Calculate dynamic color range based on current crowding levels
    if len(dest_data) > 0:
        max_crowding = max(dest_data["capacity_util"])
        # Set range to show variation (0 to max*1.2 for headroom, minimum 50% for visibility)
        dynamic_max = max(0.5, max_crowding * 1.2)
    else:
        dynamic_max = 0.5  # Default range

    # Create choropleth base
    fig = px.choropleth(
        dest_data,
        locations="country_code",
        color="capacity_util",
        color_continuous_scale="RdYlGn_r",  # Red (high) to Green (low)
        range_color=(0, dynamic_max),
        title=f"Global Tourism Map (🟢=Traveling Agents, ⬜=Home Countries)",
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

    # Add traveling agents as scatter overlay
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
                name="Traveling Agents",
            )
        )

    # Add home country markers
    home_data = get_agent_home_data(sim)
    if len(home_data) > 0:
        fig.add_trace(
            go.Scattergeo(
                lon=home_data["longitude"],
                lat=home_data["latitude"],
                mode="markers",
                marker=dict(
                    size=home_data["agent_count"] * 0.5 + 4,  # Scale with agent count
                    color="gray",
                    symbol="square",
                    line=dict(width=1, color="white"),
                    opacity=0.6,
                ),
                text=home_data["tooltip"],
                hoverinfo="text",
                name="Agent Home Countries",
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

    # Use current_date from simulation (already tracked)
    date_str = sim.current_date.strftime("%B %d")  # "January 04" (no year)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Simulation Date", value=date_str, delta=f"Day {sim.tick}")

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


def render_event_notifications(sim):
    """
    Render live event notifications as stacked banners.

    Shows blue info banners for all currently active events.
    """
    # Use current_date from simulation (already tracked)
    current_date = sim.current_date

    # Get all active events
    active_events = sim.planned_events.get_active_events(current_date)

    if active_events:
        # Stack notifications for each active event
        for event in active_events:
            days_remaining = (event.end_date - current_date).days
            end_date_str = event.end_date.strftime("Ends %b %d")

            st.info(
                f"🔵 **{event.name} is LIVE in {event.country_code}!** ({end_date_str})"
            )


def render_time_series(sim, selected_country=None):
    """Render time series chart of arrivals (global or country-specific)."""
    if selected_country and selected_country != "Global":
        # Country-specific time series
        if selected_country in sim.data_collector.dest_visitors:
            country_arrivals = sim.data_collector.dest_visitors[selected_country]
            df = pd.DataFrame(
                {
                    "Day": range(1, len(country_arrivals) + 1),
                    "Arrivals": country_arrivals,
                }
            )
            country_name = sim.destinations[selected_country].country_name
            title = f"{country_name} - Daily Arrivals"
        else:
            st.info(f"No data for {selected_country} yet.")
            return
    else:
        # Global time series
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
        title = "🌍 Global - Daily Arrivals"

    fig = px.line(
        df,
        x="Day",
        y="Arrivals",
        title=title,
        markers=False,
    )

    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="Simulation Day",
        yaxis_title="Number of Arrivals",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_country_selector(sim):
    """Render country filter dropdown."""
    countries = sorted(
        [(code, dest.country_name) for code, dest in sim.destinations.items()],
        key=lambda x: x[1],
    )

    country_options = ["Global"] + [code for code, name in countries]
    country_names = {code: name for code, name in countries}
    country_names["Global"] = "🌍 Global"

    selected = st.selectbox(
        "📍 Filter Graphs by Country",
        options=country_options,
        format_func=lambda code: country_names.get(code, code),
        index=0,
        key="country_selector",
        help="Select a country to see its specific arrival trends",
    )

    return selected


def render_top_destinations(sim):
    """Render top 10 destinations bar chart with color indicators."""
    dest_data = get_destination_data(sim)

    if len(dest_data) == 0:
        return

    # Sort by current visitors
    top_10 = dest_data.nlargest(10, "visitors")[
        ["country_name", "visitors", "capacity_util"]
    ].copy()

    # Add color indicator emoji matching map logic
    def get_crowding_emoji(ratio):
        if ratio < 0.55:
            return "🟢"  # Green (LOW)
        elif ratio < 0.80:
            return "🟡"  # Yellow (MEDIUM)
        elif ratio < 1.0:
            return "🟠"  # Orange (HIGH)
        else:
            return "🔴"  # Red (CRITICAL)

    top_10["status"] = top_10["capacity_util"].apply(get_crowding_emoji)
    top_10["display"] = top_10.apply(
        lambda row: (
            f"{row['status']} {row['country_name']} ({row['capacity_util']:.1%})"
        ),
        axis=1,
    )

    fig = px.bar(
        top_10,
        x="visitors",
        y="display",
        orientation="h",
        title="Top 10 Destinations by Current Visitors (🟢LOW 🟡MED 🟠HIGH 🔴CRIT)",
        color="capacity_util",
        color_continuous_scale="RdYlGn_r",
    )

    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="Current Visitors",
        yaxis_title="Country",
        yaxis=dict(showticklabels=True),
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
            # Agent Count Configuration
            st.subheader("👥 Simulation Settings")

            agent_count = st.slider(
                "Number of Tourist Agents",
                min_value=1000,
                max_value=100000,
                value=40000,
                step=1000,
                help="More agents = more realistic crowding dynamics, but slower simulation. "
                "4,000 agents: ~0.1s per tick | 40,000: ~1s per tick | 100,000: ~2.5s per tick",
                key="agent_count_slider",
            )

            st.divider()

            # Event Configuration Modal (only before initialization)
            with st.expander("📅 Configure Planned Events", expanded=True):
                st.write("Configure events before starting simulation")

                # Initialize event list in session state
                if "configured_events" not in st.session_state:
                    st.session_state.configured_events = [
                        {
                            "name": "FIFA World Cup 2026",
                            "country": "US",
                            "start": datetime(2026, 6, 1),
                            "end": datetime(2026, 7, 15),
                            "magnitude": 0.8,
                            "appeal": {
                                "budget": 0.6,
                                "luxury": 0.8,
                                "adventure": 0.5,
                                "family": 0.9,
                            },
                        }
                    ]

                # Show current events with remove buttons
                st.write("**Current Events:**")
                if len(st.session_state.configured_events) > 0:
                    for i, event in enumerate(st.session_state.configured_events):
                        col_evt, col_btn = st.columns([4, 1])
                        with col_evt:
                            st.info(
                                f"**{event['name']}**\n"
                                f"📍 {event['country']} | 📆 {event['start'].strftime('%b %d')} - {event['end'].strftime('%b %d')}\n"
                                f"💪 {event['magnitude'] * 100:.0f}% impact"
                            )
                        with col_btn:
                            if st.button("🗑️", key=f"remove_event_{i}"):
                                st.session_state.configured_events.pop(i)
                                st.rerun()
                else:
                    st.info("No events configured. Add your first event below!")

                st.divider()

                # Add new event form
                st.write("**➕ Add New Event**")
                new_event_name = st.text_input("Event Name", key="new_event_name")
                new_event_country = st.selectbox(
                    "Host Country",
                    options=[
                        "US",
                        "FR",
                        "ES",
                        "IT",
                        "GB",
                        "DE",
                        "CN",
                        "JP",
                        "AU",
                        "BR",
                        "MX",
                    ],
                    key="new_event_country",
                )
                col1, col2 = st.columns(2)
                with col1:
                    new_event_start = st.date_input("Start Date", key="new_event_start")
                with col2:
                    new_event_end = st.date_input("End Date", key="new_event_end")

                new_event_magnitude = st.slider("Impact Strength", 0.0, 1.0, 0.5, 0.1)

                st.write("**Segment Appeal:**")
                col_a, col_b = st.columns(2)
                with col_a:
                    appeal_budget = st.slider(
                        "Budget", 0.0, 1.0, 0.6, 0.1, key="appeal_budget"
                    )
                    appeal_luxury = st.slider(
                        "Luxury", 0.0, 1.0, 0.7, 0.1, key="appeal_luxury"
                    )
                with col_b:
                    appeal_adventure = st.slider(
                        "Adventure", 0.0, 1.0, 0.5, 0.1, key="appeal_adventure"
                    )
                    appeal_family = st.slider(
                        "Family", 0.0, 1.0, 0.8, 0.1, key="appeal_family"
                    )

                if st.button("Add Event", use_container_width=True):
                    if new_event_name:
                        st.session_state.configured_events.append(
                            {
                                "name": new_event_name,
                                "country": new_event_country,
                                "start": datetime.combine(
                                    new_event_start, datetime.min.time()
                                ),
                                "end": datetime.combine(
                                    new_event_end, datetime.min.time()
                                ),
                                "magnitude": new_event_magnitude,
                                "appeal": {
                                    "budget": appeal_budget,
                                    "luxury": appeal_luxury,
                                    "adventure": appeal_adventure,
                                    "family": appeal_family,
                                },
                            }
                        )
                        st.success(f"Added {new_event_name}!")
                        st.rerun()

            if st.button(
                "Initialize Simulation",
                type="primary",
                use_container_width=True,
                on_click=lambda: logger.info(
                    f"Initialize button clicked with {agent_count:,} agents"
                ),
                key="initialize_simulation_button",
            ):
                create_simulation(agent_count)
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
        # Control frame rate: 1 FPS at 1× speed (365 days = 6 minutes)
        frame_time = 1.0 / st.session_state.speed
        time.sleep(frame_time)

        # Run single step
        sim.step()
        st.session_state.tick += 1

        # Log progress every 100 ticks
        if st.session_state.tick % 100 == 0:
            logger.info(
                f"Simulation tick: {st.session_state.tick}, active travelers: {sim.data_collector.get_summary()['active_travelers']}"
            )

        # Render BEFORE rerun to show updates (skip map while running to prevent flicker)
        render_summary_metrics(sim)
        render_event_notifications(sim)
        render_time_series(sim)
        render_top_destinations(sim)
        render_segment_breakdown(sim)

        # Show map placeholder while running
        st.info("🗺️ Map visualization paused during run - pause simulation to see map")

        # Force rerun to continue simulation
        st.rerun()

    # Render dashboard (when paused)
    render_summary_metrics(sim)

    # Render event notifications (if any active events)
    render_event_notifications(sim)

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
        # Country filter dropdown
        selected_country = render_country_selector(sim)

        # Time series (filtered by country)
        render_time_series(sim, selected_country)

        # Top destinations
        render_top_destinations(sim)

        # Segment breakdown
        render_segment_breakdown(sim)

    # Country details panel (if selected)
    if st.session_state.selected_country:
        st.divider()
        render_destination_details(sim, st.session_state.selected_country)

    # Agent dashboard (when paused)
    if sim and not st.session_state.running:
        st.divider()
        render_agent_dashboard(sim)


def render_agent_dashboard(sim):
    """
    Render detailed agent status table (visible when paused).

    Shows:
    - Agent ID, Category, Status, Duration, Days Until Next Trip
    - Summary charts (state distribution, segment mix, top destinations)
    """
    with st.expander("👥 Sampled Agent Status (100 agents)", expanded=True):
        # Build agent data
        agent_data = []
        for agent in sim.agents:
            if agent.agent_id in sim.sampled_agent_ids:
                # Calculate duration display
                if agent.state == "STAYING":
                    duration_display = f"{agent.stay_duration}d"
                else:
                    duration_display = "-"

                # Calculate days until next trip display
                days_until_next = ""
                if agent.state == "HOME":
                    days_until_next = str(agent.days_until_next_trip)

                agent_data.append(
                    {
                        "Name": agent.agent_id,
                        "Category": agent.segment.capitalize(),
                        "Status": agent.state,
                        "Current Destination": agent.current_destination or "-",
                        "Duration": duration_display,
                        "Days Until Next Trip": days_until_next,
                    }
                )

        df = pd.DataFrame(agent_data)

        # Main table
        st.dataframe(df, use_container_width=True, height=350, hide_index=True)

        # Summary charts (3 columns)
        col1, col2, col3 = st.columns(3)

        with col1:
            # State distribution pie chart
            state_counts = df["Status"].value_counts()
            if len(state_counts) > 0:
                fig_state = px.pie(
                    values=state_counts.values,
                    names=state_counts.index,
                    title="Agent State Distribution",
                    color=state_counts.index,
                    color_discrete_map={
                        "HOME": "#1f77b4",
                        "CHOOSING": "#ff7f0e",
                        "TRAVELING": "#2ca02c",
                        "STAYING": "#d62728",
                    },
                )
                fig_state.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_state, use_container_width=True)

        with col2:
            # Segment distribution bar chart
            segment_counts = df["Category"].value_counts()
            if len(segment_counts) > 0:
                fig_segment = px.bar(
                    x=segment_counts.index,
                    y=segment_counts.values,
                    title="Segment Distribution",
                    color=segment_counts.index,
                    color_discrete_map={
                        "Budget": "#1f77b4",
                        "Luxury": "#ff7f0e",
                        "Adventure": "#2ca02c",
                        "Family": "#d62728",
                    },
                )
                fig_segment.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_segment, use_container_width=True)

        with col3:
            # Top current destinations
            staying_agents = df[df["Status"] == "STAYING"]
            if len(staying_agents) > 0:
                dest_counts = (
                    staying_agents["Current Destination"].value_counts().head(5)
                )
                fig_dest = px.bar(
                    x=dest_counts.values,
                    y=dest_counts.index,
                    orientation="h",
                    title="Top Current Destinations",
                )
                fig_dest.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_dest, use_container_width=True)


if __name__ == "__main__":
    main()
