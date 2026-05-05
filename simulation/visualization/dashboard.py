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
from simulation.data.loaders import load_country_data, load_centroids
from simulation.events.planned_events import create_fifa_world_cup_2026
from simulation.mechanics.utility import SEGMENT_WEIGHTS


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


def create_simulation(agent_count: int = 40000, start_date: datetime = None):
    """Create and initialize simulation with configured events.

    Args:
        agent_count: Number of tourist agents (default: 40,000)
        start_date: Simulation start date (default: January 1, 2026)
    """
    if start_date is None:
        start_date = datetime(2026, 1, 1)
    
    with st.spinner(f"Initializing simulation with {agent_count:,} agents starting {start_date.strftime('%B %d, %Y')}..."):
        # Clear old simulation data to prevent memory accumulation
        if st.session_state.simulation and hasattr(st.session_state.simulation, 'data_collector'):
            st.session_state.simulation.data_collector.clear()
            logger.info("Cleared old simulation data collector")
        
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
            "start_date": start_date.strftime("%Y-%m-%d"),
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
                    pre_event_days=event_config.get("pre_event_days", 30),
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
                            "state": "TRAVELING",
                        }
                    )
            elif agent.state == "CHOOSING":
                # Show CHOOSING agents at home location with purple color
                dest = sim.destinations.get(agent.home_country_code)
                if dest:
                    data.append(
                        {
                            "agent_id": agent.agent_id,
                            "segment": agent.segment,
                            "home_country": agent.home_country,
                            "current_destination": "PLANNING",
                            "days_remaining": agent.days_in_choosing,
                            "latitude": dest.latitude,
                            "longitude": dest.longitude,
                            "color": "#9b59b6",  # Purple for planning state
                            "state": "CHOOSING",
                        }
                    )
            elif agent.state == "HOME":
                # Show HOME agents at home location with gray color
                dest = sim.destinations.get(agent.home_country_code)
                if dest:
                    data.append(
                        {
                            "agent_id": agent.agent_id,
                            "segment": agent.segment,
                            "home_country": agent.home_country,
                            "current_destination": "HOME",
                            "days_remaining": agent.days_until_next_trip,
                            "latitude": dest.latitude,
                            "longitude": dest.longitude,
                            "color": "#95a5a6",  # Gray for home state
                            "state": "HOME",
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
                        f"State: {row['state']}<br>"
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


def render_country_selector(sim, key="country_selector", store_in_session=True):
    """Render country filter dropdown."""
    countries = sorted(
        [(code, dest.country_name) for code, dest in sim.destinations.items()],
        key=lambda x: x[1],
    )

    country_options = ["Global"] + [code for code, name in countries]
    country_names = {code: name for code, name in countries}
    country_names["Global"] = "🌍 Global"

    selected = st.selectbox(
        "📍 Filter by Country",
        options=country_options,
        format_func=lambda code: country_names.get(code, code),
        index=0,
        key=key,
        help="Select a country to see its specific arrival trends",
    )
    
    # Store in session state for destination details panel
    if store_in_session:
        st.session_state.selected_country = selected if selected != "Global" else None
    
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

    # Use neutral color for bars (bar length = visitors, emoji = crowding level)
    fig = px.bar(
        top_10,
        x="visitors",
        y="display",
        orientation="h",
        title="Top 10 Destinations by Current Visitors (🟢LOW 🟡MED 🟠HIGH 🔴CRIT)",
        color_discrete_sequence=["#1f77b4"],  # Neutral blue
    )

    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="Current Visitors",
        yaxis_title="Country",
        yaxis=dict(showticklabels=True),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_continent_stats(sim):
    """Render continent-level tourism distribution chart."""
    from pathlib import Path
    from simulation.data.loaders import load_centroids
    
    # Load centroids to get region data
    centroids = load_centroids(Path('data/derived'))
    
    # Aggregate by continent/region
    continent_data = {}
    
    for code, dest in sim.destinations.items():
        # Get region from centroids
        centroid = centroids.get(code, {})
        region = centroid.get('region', 'Unknown')
        
        visitors = dest.get_current_visitors()
        capacity = dest.base_capacity
        utilization = visitors / capacity if capacity > 0 else 0.0
        
        if region not in continent_data:
            continent_data[region] = {
                'visitors': 0,
                'capacity': 0,
                'countries': 0,
                'utilization_sum': 0.0,
            }
        
        continent_data[region]['visitors'] += visitors
        continent_data[region]['capacity'] += capacity
        continent_data[region]['countries'] += 1
        continent_data[region]['utilization_sum'] += utilization
    
    if not continent_data:
        st.info("No continental data available yet.")
        return
    
    # Build dataframe
    rows = []
    for region, data in continent_data.items():
        avg_utilization = data['utilization_sum'] / data['countries'] if data['countries'] > 0 else 0.0
        rows.append({
            'Continent': region,
            'Visitors': data['visitors'],
            'Capacity': data['capacity'],
            'Countries': data['countries'],
            'Utilization (%)': avg_utilization * 100,
        })
    
    df = pd.DataFrame(rows)
    
    # Create visualization
    fig = px.bar(
        df,
        x='Continent',
        y='Utilization (%)',
        title='Tourism Utilization by Continent (Visitors / Capacity)',
        color='Utilization (%)',
        color_continuous_scale='RdYlGn_r',  # Red (high) to Green (low)
        hover_data={
            'Visitors': True,
            'Capacity': True,
            'Countries': True,
            'Utilization (%)': ':.1f',
        },
    )
    
    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title='Continent',
        yaxis_title='Utilization (%)',
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show summary table below chart
    st.write("**📊 Continental Summary:**")
    st.dataframe(
        df.sort_values('Utilization (%)', ascending=False),
        use_container_width=True,
        height=200,
        hide_index=True,
    )


def render_utilization_trend(sim, country_code):
    """Render utilization percentage trend over last 90 days."""
    if country_code not in sim.data_collector.dest_capacity_util:
        st.info("No utilization data available yet.")
        return
    
    util_data = sim.data_collector.dest_capacity_util[country_code]
    
    # Get last 90 days
    last_90 = util_data[-90:] if len(util_data) > 90 else util_data
    
    if not last_90:
        st.info("No recent utilization data.")
        return
    
    # Create dataframe
    df = pd.DataFrame({
        'Day': range(len(last_90)),
        'Utilization (%)': [u * 100 for u in last_90],
    })
    
    # Determine color based on current utilization
    current_util = last_90[-1] if last_90 else 0
    if current_util > 1.0:
        line_color = '#e74c3c'  # Red (over capacity)
    elif current_util > 0.8:
        line_color = '#f39c12'  # Orange (high)
    else:
        line_color = '#27ae60'  # Green (healthy)
    
    fig = px.line(
        df,
        x='Day',
        y='Utilization (%)',
        title=f'Capacity Utilization (Last 90 Days)',
    )
    
    # Set line color
    fig.update_traces(line=dict(color=line_color, width=3))
    
    # Add threshold lines
    fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="100% Capacity")
    fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="80% Threshold")
    
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title='Days Ago',
        yaxis_title='Utilization (%)',
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_visitor_origins(sim, country_code):
    """Render pie chart of visitor origins (last 90 days)."""
    # Get trip records for this destination
    trips = [
        t for t in sim.data_collector.trip_records
        if t['destination'] == country_code
    ]
    
    if not trips:
        st.info("No visitor data available yet.")
        return
    
    # Filter to last 90 days (approximate)
    current_tick = sim.tick
    recent_trips = [
        t for t in trips
        if t['arrival_tick'] >= (current_tick - 90)
    ]
    
    if not recent_trips:
        st.info("No visitors in last 90 days.")
        return
    
    # Count by origin
    from collections import Counter
    origin_counts = Counter(t['origin'] for t in recent_trips)
    
    # Get top 10 origins
    top_origins = origin_counts.most_common(10)
    
    # Get country names for origins
    origin_names = []
    origin_values = []
    for code, count in top_origins:
        origin_dest = sim.destinations.get(code)
        name = origin_dest.country_name if origin_dest else code
        origin_names.append(name)
        origin_values.append(count)
    
    # Create dataframe
    df = pd.DataFrame({
        'Origin': origin_names,
        'Visitors': origin_values,
    })
    
    fig = px.pie(
        df,
        names='Origin',
        values='Visitors',
        title=f'Visitor Origins (Last 90 Days, n={sum(origin_values):,})',
        hole=0.3,
    )
    
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
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
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Current Visitors", 
            value=dest_dict["current_visitors"], 
            delta=None
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
    
    with col4:
        st.metric(
            label="Effective Capacity",
            value=f"{dest_dict['effective_capacity']:,}",
            delta=f"{dest_dict['base_capacity']:,} base",
        )

    # Charts section
    st.divider()
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Utilization trend (last 90 days)
        render_utilization_trend(sim, country_code)
    
    with col_chart2:
        # Visitor origins pie chart (last 90 days)
        render_visitor_origins(sim, country_code)

    # Additional details
    st.divider()
    with st.expander("📋 Detailed Information", expanded=False):
        st.write(f"**Country Code**: {dest_dict['country_code']}")
        st.write(f"**Base Capacity**: {dest_dict['base_capacity']:,}")
        st.write(f"**Effective Capacity**: {dest_dict['effective_capacity']:,}")
        st.write(f"**Attractiveness Score**: {dest_dict['attractiveness']:.2f}")
        st.write(f"**Cost Index**: {dest_dict['cost_index']:.1f}")
        st.write(f"**Risk Score**: {dest_dict['risk_score']:.2f}")
        st.write(f"**Climate Zone**: {dest_dict['climate_zone']}")
        st.write(f"**Current TFI**: {dest_dict['tfi']:.3f}")
        st.write(f"**TFI Trend**: {dest_dict['tfi_trend']}")

    # Policy suggestions
    suggestions = dest.get_rectification_suggestions()
    if suggestions:
        st.divider()
        st.warning("⚠️ **Policy Recommendations**:")
        for suggestion in suggestions:
            st.write(f"- {suggestion}")


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

    def trigger_negative_event(country_code, event_type, severity, duration_days):
        """Trigger a negative event in specified country"""
        event_names = {
            "disaster": "Natural Disaster",
            "epidemic": "Epidemic Outbreak",
            "political_unrest": "Political Unrest",
            "economic_shock": "Economic Crisis",
            "terrorism": "Terrorist Attack",
        }
        
        event_name = event_names.get(event_type, event_type.replace("_", " ").title())
        
        st.session_state.simulation.unplanned_events.trigger_event(
            country_code=country_code,
            event_type=event_type,
            severity=severity,
            current_date=st.session_state.simulation.current_date,
            duration_days=duration_days,
            name=f"{event_name} in {country_code}",
        )
        
        dest = st.session_state.simulation.destinations.get(country_code)
        country_name = dest.country_name if dest else country_code
        
        logger.info(f"{event_name} triggered in {country_code} (severity: {severity}, duration: {duration_days}d)")
        st.success(f"⚠️ {event_name} triggered in {country_name}!")

    def step_simulation(sim_obj):
        """Advance simulation by one day"""
        sim_obj.step()
        st.session_state.tick += 1
        logger.info(f"Manual step: tick {st.session_state.tick}")

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

            # Start Date Configuration
            start_date = st.date_input(
                "Simulation Start Date",
                value=datetime(2026, 1, 1),
                min_value=datetime(2026, 1, 1),
                max_value=datetime(2030, 12, 31),
                help="Choose when to start the simulation. Events like FIFA World Cup are scheduled relative to this date.",
                key="start_date_picker",
            )

            # Random Seed Configuration
            seed = st.number_input(
                "Random Seed",
                min_value=1,
                max_value=999999,
                value=42,
                step=1,
                help="Seed for reproducibility. Same seed = identical simulation results. Use different seeds for varied outcomes.",
                key="seed_input",
            )

            st.divider()

            # Event Configuration Modal (only before initialization)
            with st.expander("📅 Configure Planned Events", expanded=True):
                st.write("Configure events before starting simulation")
                st.info("ℹ️ Events are scheduled on fixed calendar dates. If your start date is after an event, it won't occur during the simulation.")

                # Initialize event list in session state
                if "configured_events" not in st.session_state:
                    st.session_state.configured_events = [
                        {
                            "name": "FIFA World Cup 2026",
                            "country": "USA",  # Use ISO3 code to match destination data
                            "start": datetime(2026, 6, 1),
                            "end": datetime(2026, 7, 15),
                            "magnitude": 0.8,
                            "appeal": {
                                "budget": 0.6,
                                "luxury": 0.8,
                                "adventure": 0.5,
                                "family": 0.9,
                            },
                            "pre_event_days": 45,  # Start ramp-up from April 17
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
                        "USA",
                        "FRA",
                        "ESP",
                        "ITA",
                        "GBR",
                        "DEU",
                        "CHN",
                        "JPN",
                        "AUS",
                        "BRA",
                        "MEX",
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

                # Pre-event days input
                pre_event_days = st.slider(
                    "Pre-event ramp-up (days)", 0, 90, 45, 5, key="pre_event_days"
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
                                "pre_event_days": pre_event_days,
                            }
                        )
                        st.success(f"Added {new_event_name}!")
                        st.rerun()

            if st.button(
                "Initialize Simulation",
                type="primary",
                use_container_width=True,
                on_click=lambda: logger.info(
                    f"Initialize button clicked with {agent_count:,} agents starting {start_date}"
                ),
                key="initialize_simulation_button",
            ):
                create_simulation(agent_count, start_date)
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

            # Control buttons row 2: Step and Run-to-Date
            col_step, col_runto = st.columns([1, 2])
            
            with col_step:
                st.button(
                    "⏭️ Step (1 day)",
                    use_container_width=True,
                    on_click=lambda: step_simulation(st.session_state.simulation),
                    disabled=st.session_state.running,
                )
            
            with col_runto:
                # Run to specific date
                sim_obj = st.session_state.get('simulation')
                if sim_obj:
                    current_date = sim_obj.current_date
                    target_date = st.date_input(
                        "Run to:",
                        value=current_date + timedelta(days=30),
                        min_value=current_date,
                        max_value=current_date + timedelta(days=365),
                        key="target_date_picker",
                        label_visibility="collapsed",
                    )
                    
                    if st.button("⏩ Run to Date", use_container_width=True):
                        st.session_state.run_to_target = target_date
                        st.session_state.running = True
                else:
                    st.write("Initialize simulation first")

            # Speed control
            speed = st.select_slider(
                "Simulation Speed",
                options=[0.5, 1.0, 2.0, 4.0, 10.0],
                value=st.session_state.speed,
                key="speed_slider",
            )
            st.session_state.speed = speed

            # Memory monitoring
            st.divider()
            st.subheader("💾 System")
            
            try:
                import psutil
                import os
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                # Color coding based on usage
                if memory_mb > 2000:
                    st.error(f"⚠️ RAM Usage: **{memory_mb:.0f} MB**")
                    st.warning("High memory usage! Consider refreshing the page.")
                elif memory_mb > 1000:
                    st.warning(f"⚡ RAM Usage: **{memory_mb:.0f} MB**")
                else:
                    st.success(f"✅ RAM Usage: **{memory_mb:.0f} MB**")
                
                # Show memory stats from data collector
                if st.session_state.simulation:
                    mem_stats = st.session_state.simulation.data_collector.get_memory_stats()
                    with st.expander("📊 Memory Details"):
                        st.write(f"**Day:** {mem_stats['tick']}")
                        st.write(f"**Data points:**")
                        st.write(f"  - Visitors: {mem_stats['visitor_points']:,}")
                        st.write(f"  - Trajectories: {mem_stats['trajectory_points']:,}")
                        st.write(f"  - Trip records: {mem_stats['trip_records']:,}")
                        st.write(f"**Estimated collector memory:** {mem_stats['estimated_mb']:.2f} MB")
                        st.write(f"**Limits:** {mem_stats['limits']['max_days']} days, {mem_stats['limits']['max_trajectories']} trajectories, {mem_stats['limits']['max_trip_records']:,} trips")
            except ImportError:
                st.info("Install psutil for memory monitoring: `pip install psutil`")

            # Trigger negative event
            st.divider()
            st.subheader("⚠️ Trigger Negative Event")

            # Country selector
            sim_countries = list(st.session_state.simulation.destinations.items())
            sim_countries.sort(key=lambda x: x[1].country_name)
            
            country_options = {f"{dest.country_name} ({code})": code for code, dest in sim_countries}
            
            selected_country_display = st.selectbox(
                "Target Country",
                options=list(country_options.keys()),
                help="Select the country to affect",
                key="negative_event_country",
            )
            
            # Event type selector
            event_types = {
                "🌋 Natural Disaster": "disaster",
                "🦠 Epidemic Outbreak": "epidemic",
                "🔥 Political Unrest": "political_unrest",
                "💰 Economic Crisis": "economic_shock",
                "💣 Terrorist Attack": "terrorism",
            }
            
            selected_event_display = st.selectbox(
                "Event Type",
                options=list(event_types.keys()),
                help="Select the type of negative event",
                key="negative_event_type",
            )
            
            # Severity selector
            severity_options = {
                "Low (0.3)": 0.3,
                "Medium (0.5)": 0.5,
                "High (0.7)": 0.7,
                "Critical (0.9)": 0.9,
            }
            
            selected_severity_display = st.selectbox(
                "Severity",
                options=list(severity_options.keys()),
                help="Higher severity = stronger impact on tourist behavior",
                key="negative_event_severity",
            )
            
            # Duration selector
            duration_options = {
                "Short (30 days)": 30,
                "Medium (60 days)": 60,
                "Long (90 days)": 90,
                "Extended (180 days)": 180,
            }
            
            selected_duration_display = st.selectbox(
                "Duration",
                options=list(duration_options.keys()),
                help="How long the event affects tourist behavior",
                key="negative_event_duration",
            )
            
            # Trigger button
            if st.button(
                "⚡ Trigger Event",
                use_container_width=True,
                type="primary",
                key="trigger_negative_event",
            ):
                if selected_country_display and selected_event_display:
                    country_code = country_options[selected_country_display]
                    event_type = event_types[selected_event_display]
                    severity = severity_options[selected_severity_display]
                    duration = duration_options[selected_duration_display]
                    
                    trigger_negative_event(country_code, event_type, severity, duration)
                else:
                    st.error("Please select both country and event type")

    # Main content area
    if st.session_state.simulation is None:
        # Welcome screen
        st.info("👈 Configure and click **'Initialize Simulation'** in the sidebar to begin.")

        st.markdown("""
        ### Features:
        - **Configurable tourist agents** (1,000 - 100,000) with segment-specific behavior
          - Budget (30%), Luxury (20%), Adventure (25%), Family (25%)
          - Trips per year vary by segment (0.75 - 2.0 trips)
        - **177 countries** with realistic hotel capacity and TFI dynamics
          - Capacity derived from UN Tourism arrival data
          - Tourism Friendliness Index responds to crowding
          - GDP dependency modifies TFI dynamics
        - **Planned events** (e.g., FIFA World Cup, Olympics)
          - Pre-event ramp-up (up to 90 days before)
          - Event period impact (bell curve distribution)
          - Post-event decline (15 days)
        - **Unplanned events** (disasters, epidemics)
          - Dynamic risk multipliers affecting destination choice
        - **Real-time visualization** of tourism flows
          - Interactive choropleth map
          - Agent-level tracking (100 sampled agents)
          - Diagnostic logging every 100 days
        
        ### How to Use:
        1. **Configure simulation** in sidebar:
           - Choose number of agents (more = realistic crowding, slower)
           - Set start date (events scheduled relative to this)
           - Add/modify planned events
        2. Click **Initialize Simulation**
        3. Click **▶️ Run** to start
        4. Watch agents travel between countries
        5. Click on countries for details
        6. Trigger events to see impacts
        7. **Pause** to explore agent dashboard
        
        ### Tips:
        - **40,000 agents** recommended for balance of speed/realism
        - Run to **Day 150+** to see FIFA World Cup impact (if starting Jan 1)
        - Check **diagnostic logs** in console every 100 days
        - **Agent dashboard** shows detailed status when paused
        """)

        return

    # Get simulation object
    sim = st.session_state.get('simulation')
    
    if not sim:
        st.warning("Simulation not initialized. Please click 'Initialize Simulation' in the sidebar.")
        return

    # Run simulation step if active
    if st.session_state.running:
        # Check if running to target date (batch mode - no rendering delays)
        target_date = st.session_state.get('run_to_target')
        
        if target_date:
            # Convert date to datetime for comparison (st.date_input returns date, sim uses datetime)
            target_datetime = datetime.combine(target_date, datetime.min.time())
            start_tick = sim.tick
            total_ticks = (target_datetime - sim.current_date).days
            
            # Create progress bar and status message
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.info(f"🚀 Running batch simulation: Day {start_tick} → Day {start_tick + total_ticks}")
            
            # Run in batch mode with progress tracking
            ticks_per_log = max(1, total_ticks // 20)  # Log every 5% of progress
            batch_start_time = time.time()
            
            while sim.current_date < target_datetime:
                sim.step()
                st.session_state.tick += 1
                
                # Update progress every 5%
                current_progress = (sim.tick - start_tick) / total_ticks
                if current_progress <= 1.0:
                    progress_bar.progress(current_progress)
                
                # Log key metrics at intervals
                if (sim.tick - start_tick) % ticks_per_log == 0:
                    summary = sim.data_collector.get_summary()
                    elapsed = time.time() - batch_start_time
                    ticks_per_sec = (sim.tick - start_tick) / elapsed if elapsed > 0 else 0
                    
                    status_text.info(
                        f"⏳ Day {sim.tick}/{start_tick + total_ticks} | "
                        f"Travelers: {summary['active_travelers']:,} | "
                        f"Speed: {ticks_per_sec:.0f} ticks/sec"
                    )
                    
                    # Log detailed metrics for analysis
                    logger.info(
                        f"BATCH PROGRESS: tick={sim.tick}, "
                        f"date={sim.current_date.strftime('%Y-%m-%d')}, "
                        f"active_travelers={summary['active_travelers']:,}, "
                        f"speed={ticks_per_sec:.1f} ticks/sec"
                    )
            
            # Final log with performance summary
            batch_end_time = time.time()
            total_time = batch_end_time - batch_start_time
            final_summary = sim.data_collector.get_summary()
            
            logger.info(
                f"BATCH COMPLETE: "
                f"ticks_executed={total_ticks}, "
                f"total_time={total_time:.2f}s, "
                f"avg_speed={total_ticks/total_time:.1f} ticks/sec, "
                f"final_active_travelers={final_summary['active_travelers']:,}, "
                f"final_date={sim.current_date.strftime('%Y-%m-%d')}"
            )
            
            # Update progress to 100%
            progress_bar.progress(1.0)
            status_text.success(
                f"✅ Completed {total_ticks} days in {total_time:.2f}s "
                f"({total_ticks/total_time:.0f} ticks/sec)"
            )
            
            # Reached target - stop and clear target
            st.session_state.running = False
            st.session_state.run_to_target = None
            
            # Brief pause to show completion message
            time.sleep(1.5)
            st.rerun()
        else:
            # Normal real-time mode with frame rate control
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

    # Render dashboard with tabbed organization (when paused)
    render_summary_metrics(sim)

    # Render event notifications (if any active events)
    render_event_notifications(sim)

    st.divider()

    # Main dashboard tabs
    tab_overview, tab_agents, tab_destinations, tab_analytics, tab_settings = st.tabs([
        "🗺️ Overview",
        "👥 Agents",
        "🏨 Destinations",
        "📈 Analytics",
        "⚙️ Settings",
    ])

    with tab_overview:
        st.header("🗺️ Global Overview")
        
        # Map - Full width (no obstruction)
        fig_map = render_map(sim)
        st.plotly_chart(fig_map, use_container_width=True, key="map")
        
        # Continent-level statistics below map
        st.divider()
        st.subheader("🌍 Continental Tourism Distribution")
        render_continent_stats(sim)
        
        # Note: For country-specific details, use the Destinations tab
        st.info("💡 **Tip**: Select a specific country in the 🏨 Destinations tab for detailed analysis")

    with tab_agents:
        st.header("👥 Agent Analysis")
        
        if not st.session_state.running:
            render_agent_dashboard(sim)
        else:
            st.info("⏸️ Pause simulation to view detailed agent dashboard")
            
            # Show mini summary even while running
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Sampled Agents", f"{len(sim.sampled_agent_ids):,}")
            with col2:
                summary = sim.data_collector.get_summary()
                st.metric("Active Travelers", f"{summary['active_travelers']:,}")

    with tab_destinations:
        st.header("🏨 Destination Details")
        
        # Country selector at top
        selected_country = render_country_selector(sim, key="dest_selector")
        
        if selected_country and selected_country != "Global":
            # Show comprehensive destination details
            render_destination_details(sim, selected_country)
        else:
            # Show overview with time series and top destinations
            st.info("👈 Select a country from the dropdown above for detailed analysis")
            
            st.divider()
            
            # Time series and top destinations
            col1, col2 = st.columns([2, 1])
            
            with col1:
                render_time_series(sim, "Global")
            
            with col2:
                render_top_destinations(sim)
                st.divider()
                render_segment_breakdown(sim)

    with tab_analytics:
        st.header("📈 Analytics & Insights")
        
        # What-if analysis and complexity metrics
        st.markdown("""
        ### System Dynamics Analysis
        
        This section shows emergent patterns and feedback loops in the tourism system.
        """)
        
        if not st.session_state.running:
            # Calculate Gini coefficient for utilization inequality
            gini_coefficient = calculate_gini_coefficient(sim)
            
            # Create analytics charts in tabs
            tab_capacity, tab_tfi, tab_inequality, tab_events = st.tabs([
                "🏗️ Capacity Dynamics",
                "🔄 TFI Feedback",
                "📊 Inequality (Gini)",
                "⚡ Event Impact"
            ])
            
            with tab_capacity:
                render_capacity_dynamics(sim)
            
            with tab_tfi:
                render_tfi_feedback_chart(sim)
            
            with tab_inequality:
                render_gini_chart(sim, gini_coefficient)
            
            with tab_events:
                render_event_impact_analysis(sim)
            
            # Show what-if analysis from agent decisions if available
            st.divider()
            st.subheader("🧠 Recent Decision Analysis")
            st.write("Select an agent in CHOOSING state from the Agents tab to see decision breakdown with what-if analysis.")
        else:
            st.info("⏸️ Pause simulation to view analytics charts")

    with tab_settings:
        st.header("⚙️ Simulation Settings")
        
        st.markdown("""
        ### Event Management
        
        Trigger negative events to test system resilience and policy responses.
        """)
        
        # Show negative event trigger (moved from sidebar)
        # Note: Keep in sidebar for now, add reference here
        st.info("⬅️ Use the sidebar to trigger negative events and configure simulation parameters")
        
        # Memory monitoring
        st.divider()
        st.subheader("💾 System Monitoring")
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("RAM Usage", f"{mem_info.rss / 1024 / 1024:.1f} MB")
            with col2:
                st.metric("CPU Usage", f"{process.cpu_percent():.1f}%")
        except ImportError:
            st.info("Install psutil for system monitoring: `pip install psutil`")


def render_agent_dashboard(sim):
    """
    Render detailed agent status table (visible when paused).

    Shows:
    - Agent ID, Category, Status, Duration, Days Until Next Trip
    - Summary charts (state distribution, segment mix, top destinations)
    - Journey path filter with mini-map (Phase 3)
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
                elif agent.state == "CHOOSING":
                    days_until_next = f"Planning: {agent.days_in_choosing}d left"

                # Show destination with clear status for CHOOSING state
                if agent.state == "CHOOSING":
                    # Show that decision is made but distinguish from actual travel
                    current_dest_display = f"Planning... (departs in {agent.days_in_choosing}d)"
                else:
                    current_dest_display = agent.current_destination or "-"

                agent_data.append(
                    {
                        "Name": agent.agent_id,
                        "Category": agent.segment.capitalize(),
                        "Status": agent.state,
                        "Current Destination": current_dest_display,
                        "Duration": duration_display,
                        "Days Until Next Trip": days_until_next,
                        "Home Country": agent.home_country,  # Now stores country name directly
                    }
                )

        df = pd.DataFrame(agent_data)

        # Create tabs for different views
        tab1, tab2 = st.tabs(["📋 All Agents", "🔍 Filter by Agent"])

        with tab1:
            # Main table with all agents - add selection column
            st.write("**💡 Tip:** Click an agent's name to view their detailed journey")
            
            # Add selection buttons
            df_with_select = df.copy()
            
            # Create selection interface
            selected_agent_id = None
            
            # Display agent IDs as clickable links
            agent_ids = df["Name"].tolist()
            
            # Use selectbox for agent selection (Streamlit doesn't support row clicks)
            selected_agent_id = st.selectbox(
                "Quick Select Agent:",
                options=[""] + agent_ids,
                format_func=lambda x: f"👤 {x}" if x else "— Choose an agent —",
                key="quick_agent_select",
                help="Select an agent to automatically switch to their detailed view"
            )
            
            # Auto-switch to Filter tab when agent selected
            if selected_agent_id:
                st.session_state.selected_agent_for_filter = selected_agent_id
                st.info(f"✅ Selected **{selected_agent_id}** - Scroll down to '🔍 Filter by Agent' tab to view details")
            
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
                            "CHOOSING": "#9b59b6",  # Purple for planning
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

        with tab2:
            # Filter by individual agent
            st.write("**Select an agent to view their journey:**")
            
            # Check if agent was pre-selected from All Agents tab
            default_index = 0
            if hasattr(st.session_state, 'selected_agent_for_filter') and st.session_state.selected_agent_for_filter:
                # Pre-select the agent that was clicked
                agent_list = sorted(df["Name"].unique())
                if st.session_state.selected_agent_for_filter in agent_list:
                    default_index = agent_list.index(st.session_state.selected_agent_for_filter)
            
            selected_agent = st.selectbox(
                "Agent:",
                options=sorted(df["Name"].unique()),
                index=default_index,
                help="Choose an agent to view their complete journey trajectory",
                key="filter_agent_selectbox"
            )
            
            # Clear the pre-selection after using it
            if hasattr(st.session_state, 'selected_agent_for_filter'):
                st.session_state.selected_agent_for_filter = None
            
            if selected_agent:
                # Get agent data
                agent_row = df[df["Name"] == selected_agent].iloc[0]
                agent = next(a for a in sim.agents if a.agent_id == selected_agent)
                
                # Display current status
                col_status1, col_status2, col_status3 = st.columns(3)
                with col_status1:
                    st.metric("Status", agent_row["Status"])
                with col_status2:
                    st.metric("Segment", agent_row["Category"])
                with col_status3:
                    st.metric("Current Location", agent_row["Current Destination"])
                
                # Show decision breakdown if agent is CHOOSING
                if agent.state == "CHOOSING" and hasattr(agent, 'last_decision') and agent.last_decision:
                    st.divider()
                    render_decision_breakdown(agent.last_decision, sim)
                
                st.divider()
                
                # Get journey trajectory from data collector
                trajectory = sim.data_collector.agent_trajectories.get(selected_agent, [])
                
                # Build journey table with trip details
                if len(trajectory) > 0:
                    st.write("**🗺️ Journey Trajectory:**")
                    
                    # Group consecutive visits to same destination into trips
                    trips = []
                    if len(trajectory) > 0:
                        current_trip_start = trajectory[0]
                        prev_dest = trajectory[0][1]
                        
                        for i in range(1, len(trajectory)):
                            tick, dest = trajectory[i]
                            if dest != prev_dest:
                                # End current trip, start new one
                                trips.append((current_trip_start[0], trajectory[i-1][0], prev_dest))
                                current_trip_start = trajectory[i]
                            prev_dest = dest
                        
                        # Add final trip
                        trips.append((current_trip_start[0], trajectory[-1][0], prev_dest))
                    
                    # Create journey dataframe
                    journey_data = []
                    for start_tick, end_tick, dest_code in trips:
                        dest = sim.destinations.get(dest_code)
                        dest_name = dest.country_name if dest else dest_code
                        duration = end_tick - start_tick + 1
                        journey_data.append({
                            "Day": f"{start_tick} → {end_tick}",
                            "Destination": f"{dest_name} ({dest_code})",
                            "Duration": f"{duration}d",
                        })
                    
                    journey_df = pd.DataFrame(journey_data)
                    st.dataframe(journey_df, use_container_width=True, height=300, hide_index=True)
                    
                    # Render mini-map
                    st.write("**📍 Journey Path:**")
                    # Look up country code from name for mini-map (agent.home_country is now country name)
                    home_code = agent.home_country_code  # Use the stored code directly
                    render_mini_map(trajectory, home_code, sim)
                else:
                    st.info("📭 No journey data yet - agent hasn't started traveling")
                    
                    # Still show home country on map
                    st.write("**🏠 Home Location:**")
                    home_code = agent.home_country_code  # Use the stored code directly
                    render_mini_map([], home_code, sim)


def render_mini_map(trajectory: list, home_country: str, sim):
    """
    Render mini-map showing single agent's journey path.
    
    Args:
        trajectory: List of (tick, country_code) tuples
        home_country: Agent's home country code (numeric M49 code like '156', '840')
        sim: Simulation object (for country coordinates)
    """
    # Build journey data with coordinates
    journey_data = []
    
    # Add home country as starting point
    home_dest = sim.destinations.get(home_country)
    if home_dest:
        journey_data.append({
            "tick": -1,  # Before simulation start
            "country_code": home_country,
            "country_name": home_dest.country_name,
            "lat": home_dest.latitude,
            "lon": home_dest.longitude,
            "is_home": True,
        })
    
    # Add trajectory points
    for tick, country_code in trajectory:
        dest = sim.destinations.get(country_code)
        if dest:
            journey_data.append({
                "tick": tick,
                "country_code": country_code,
                "country_name": dest.country_name,
                "lat": dest.latitude,
                "lon": dest.longitude,
                "is_home": False,
            })
    
    if len(journey_data) == 0:
        st.info("No location data available")
        return
    
    journey_df = pd.DataFrame(journey_data)
    
    # Create figure
    fig = go.Figure()
    
    # Path lines (connect all points in order)
    if len(journey_df) > 1:
        fig.add_trace(go.Scattergeo(
            lon=journey_df["lon"],
            lat=journey_df["lat"],
            mode="lines",
            line=dict(width=2, color="#1f77b4"),
            name="Journey Path",
            hoverinfo="skip",
        ))
    
    # Home country marker (green square)
    home_data = journey_df[journey_df["is_home"] == True]
    if len(home_data) > 0:
        home = home_data.iloc[0]
        fig.add_trace(go.Scattergeo(
            lon=[home["lon"]],
            lat=[home["lat"]],
            mode="markers+text",
            marker=dict(size=12, color="#2ca02c", symbol="square"),
            text=[f"🏠 {home['country_name']}"],
            textposition="bottom center",
            name="Home Country",
        ))
    
    # Current location marker (red circle, largest)
    if len(trajectory) > 0:
        current = journey_df.iloc[-1]
        fig.add_trace(go.Scattergeo(
            lon=[current["lon"]],
            lat=[current["lat"]],
            mode="markers+text",
            marker=dict(size=18, color="#d62728", symbol="circle"),
            text=[f"📍 {current['country_name']}"],
            textposition="top center",
            name="Current Location",
        ))
    
    # Calculate map bounds for auto-zoom
    if len(journey_df) > 1:
        # Get bounding box of visited locations
        lon_min = journey_df["lon"].min()
        lon_max = journey_df["lon"].max()
        lat_min = journey_df["lat"].min()
        lat_max = journey_df["lat"].max()
        
        # Add padding (50% of range)
        lon_range = lon_max - lon_min
        lat_range = lat_max - lat_min
        lon_padding = max(lon_range * 0.5, 30)  # Minimum 30 degrees
        lat_padding = max(lat_range * 0.5, 20)  # Minimum 20 degrees
        
        # Center the view
        lon_center = (lon_min + lon_max) / 2
        lat_center = (lat_min + lat_max) / 2
        
        # Set projection scale based on spread
        if lon_range < 20 and lat_range < 15:
            # Regional view (small area)
            projection_scale = 8
        elif lon_range < 60 and lat_range < 40:
            # Sub-continental view
            projection_scale = 4
        else:
            # Continental/global view
            projection_scale = 2
        
        fig.update_layout(
            geo=dict(
                projection=dict(
                    type="natural earth",
                    scale=projection_scale,
                ),
                center=dict(lon=lon_center, lat=lat_center),
                scope="world",
                showland=True,
                landcolor="#f0f0f0",
                countrycolor="#cccccc",
                showcountries=True,
                bgcolor="#ffffff",
            ),
            height=450,
            margin=dict(l=0, r=0, t=40, b=0),
            title="Agent Journey Path (Auto-zoomed to visited region)",
        )
    else:
        # Single location - show world view centered on that point
        single = journey_df.iloc[0]
        fig.update_layout(
            geo=dict(
                projection=dict(type="natural earth", scale=2),
                center=dict(lon=single["lon"], lat=single["lat"]),
                scope="world",
                showland=True,
                landcolor="#f0f0f0",
                countrycolor="#cccccc",
                showcountries=True,
                bgcolor="#ffffff",
            ),
            height=450,
            margin=dict(l=0, r=0, t=40, b=0),
            title="Location Map",
        )
    
    st.plotly_chart(fig, use_container_width=True)


def render_decision_map(top_destinations: list, home_country_code: str, chosen_code: str):
    """
    Render geographic map showing top destination options.
    
    Args:
        top_destinations: List of top 10 destination dicts
        home_country_code: Agent's home country code
        chosen_code: Chosen destination country code
    """
    from simulation.data.loaders import load_centroids
    from pathlib import Path
    
    # Load centroids for coordinates
    centroids = load_centroids(Path('data/derived'))
    
    # Build marker data
    markers = []
    
    # Add home country (green)
    home_centroid = centroids.get(home_country_code)
    if home_centroid:
        markers.append({
            'lat': home_centroid['lat'],
            'lon': home_centroid['lon'],
            'type': 'home',
            'label': f"🏠 Home",
            'size': 12,
            'color': '#27ae60',
        })
    
    # Add top 10 destinations
    for i, dest in enumerate(top_destinations):
        dest_centroid = centroids.get(dest['country_code'])
        if dest_centroid:
            is_chosen = dest['country_code'] == chosen_code
            markers.append({
                'lat': dest_centroid['lat'],
                'lon': dest_centroid['lon'],
                'type': 'chosen' if is_chosen else 'option',
                'label': f"{'✅ ' if is_chosen else ''}{dest['country_name']} ({dest['probability']:.1%})",
                'size': 14 if is_chosen else 8,
                'color': '#e74c3c' if is_chosen else '#9b59b6',
                'rank': i + 1,
            })
    
    if not markers:
        st.warning("No location data available for map")
        return
    
    # Create map
    fig = go.Figure()
    
    # Add home marker
    home_markers = [m for m in markers if m['type'] == 'home']
    if home_markers:
        fig.add_trace(go.Scattergeo(
            lon=[m['lon'] for m in home_markers],
            lat=[m['lat'] for m in home_markers],
            mode='markers+text',
            marker=dict(size=12, color='#27ae60', symbol='circle', line=dict(width=1, color='white')),
            text=[m['label'] for m in home_markers],
            textposition='top center',
            name='Home',
            hoverinfo='text',
        ))
    
    # Add chosen destination marker
    chosen_markers = [m for m in markers if m['type'] == 'chosen']
    if chosen_markers:
        fig.add_trace(go.Scattergeo(
            lon=[m['lon'] for m in chosen_markers],
            lat=[m['lat'] for m in chosen_markers],
            mode='markers+text',
            marker=dict(size=14, color='#e74c3c', symbol='circle', line=dict(width=2, color='white')),
            text=[m['label'] for m in chosen_markers],
            textposition='top center',
            name='Chosen',
            hoverinfo='text',
        ))
    
    # Add other options
    option_markers = [m for m in markers if m['type'] == 'option']
    if option_markers:
        fig.add_trace(go.Scattergeo(
            lon=[m['lon'] for m in option_markers],
            lat=[m['lat'] for m in option_markers],
            mode='markers',
            marker=dict(size=8, color='#9b59b6', symbol='circle', line=dict(width=1, color='white')),
            text=[m['label'] for m in option_markers],
            name='Other Options',
            hoverinfo='text',
        ))
    
    # Calculate bounds for auto-zoom
    lats = [m['lat'] for m in markers]
    lons = [m['lon'] for m in markers]
    
    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)
    
    # Add padding
    lat_padding = max(lat_range * 0.3, 15)
    lon_padding = max(lon_range * 0.3, 20)
    
    # Center view
    lat_center = sum(lats) / len(lats)
    lon_center = sum(lons) / len(lons)
    
    # Determine scale based on spread
    if lat_range < 20 and lon_range < 30:
        scale = 8  # Regional view
    elif lat_range < 50 and lon_range < 60:
        scale = 4  # Sub-continental
    else:
        scale = 2  # Continental/global
    
    fig.update_layout(
        geo=dict(
            projection=dict(type='natural earth', scale=scale),
            center=dict(lon=lon_center, lat=lat_center),
            scope='world',
            showland=True,
            landcolor='#f0f0f0',
            countrycolor='#cccccc',
            showcountries=True,
            bgcolor='#ffffff',
        ),
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        title=f"Top 10 Destination Options (Green=Home, Red=Chosen, Purple=Alternatives)",
        legend=dict(orientation='h', y=1.05, x=0),
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_decision_breakdown(decision: dict, sim):
    """
    Render decision breakdown showing utility factors.
    
    Args:
        decision: Decision data dict with destinations, factors, chosen
        sim: Simulation object (for current tick and destination data)
    """
    st.subheader(f"🧠 Decision Breakdown: {decision['agent_id']}")
    
    # Header metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Segment", decision['segment'].capitalize())
    with col2:
        st.metric("Home Country", decision['home_country'])
    with col3:
        chosen_name = decision['chosen']
        if chosen_name:
            dest = next((d for d in decision['destinations'] if d['country_code'] == chosen_name), None)
            if dest:
                chosen_name = f"{dest['country_name']} ({chosen_name})"
        st.metric("Chosen Destination", chosen_name or "N/A")
    
    # Top choices table - show chosen destination even if outside top 10
    st.write("**📊 Destination Choice Analysis:**")
    
    chosen_code = decision['chosen']
    all_dests = decision['destinations']
    
    # Find chosen destination position
    chosen_dest = next((d for d in all_dests if d['country_code'] == chosen_code), None)
    chosen_rank = None
    if chosen_dest:
        chosen_rank = all_dests.index(chosen_dest) + 1
    
    # Show chosen destination highlight if outside top 10
    if chosen_rank and chosen_rank > 10:
        st.info(f"🎯 **Chosen destination ranked #{chosen_rank}**: {chosen_dest['country_name']} ({chosen_code}) with {chosen_dest['probability']:.2%} probability")
        st.write("*Note: Lower-probability destinations can still be selected through probabilistic choice - this demonstrates exploration behavior!*")
    
    # Build table showing top 10 PLUS chosen destination if outside top 10
    table_dests = all_dests[:10].copy()
    
    # Add chosen destination if not already in top 10
    if chosen_rank and chosen_rank > 10 and chosen_dest:
        table_dests.append(chosen_dest)
    
    # Sort by rank for display
    table_dests.sort(key=lambda x: all_dests.index(x))
    
    table_data = []
    for i, dest in enumerate(table_dests):
        is_chosen = dest['country_code'] == decision['chosen']
        rank = all_dests.index(dest) + 1
        table_data.append({
            "Rank": rank,
            "Destination": f"{dest['country_name']} ({dest['country_code']})",
            "Utility": f"{dest['utility']:.3f}",
            "Probability": f"{dest['probability']:.2%}",
            "Chosen": "✅" if is_chosen else "",
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, height=320, hide_index=True)
    
    # What-if analysis: Show how rankings would differ if choosing today
    if decision['tick'] < sim.tick:
        st.write("**🔄 What-If: Current Rankings (Day {})**".format(sim.tick))
        st.caption("*Rankings if agent were choosing today vs. original decision on Day {}*".format(decision['tick']))
        
        # Recalculate utilities for top 10 destinations using current crowding
        current_rankings = []
        for dest_code in [d['country_code'] for d in all_dests[:10]]:
            dest = sim.destinations.get(dest_code)
            if dest:
                # Recalculate crowding with current visitors
                current_crowding = dest.get_crowding_ratio()
                
                # Find original factor data
                orig_data = next((d for d in all_dests if d['country_code'] == dest_code), None)
                if orig_data:
                    # Recalculate utility with new crowding
                    weights = SEGMENT_WEIGHTS.get(decision['segment'], SEGMENT_WEIGHTS['budget'])
                    new_crowding_factor = -weights["γ"] * current_crowding
                    
                    # Approximate new utility (keeping other factors constant)
                    utility_change = new_crowding_factor - orig_data['crowding']
                    new_utility = orig_data['utility'] + utility_change
                    
                    crowding_change = current_crowding - (abs(orig_data['crowding']) / weights["γ"])
                    
                    current_rankings.append({
                        "Destination": dest.country_name,
                        "Original Rank": all_dests.index(orig_data) + 1,
                        "Crowding Change": f"{crowding_change:+.1%}",
                        "Est. New Utility": f"{new_utility:.3f}",
                    })
        
        if current_rankings:
            current_df = pd.DataFrame(current_rankings)
            current_df = current_df.sort_values("Est. New Utility", ascending=False)
            current_df["Current Rank"] = range(1, len(current_df) + 1)
            current_df = current_df[["Current Rank", "Destination", "Original Rank", "Crowding Change", "Est. New Utility"]]
            st.dataframe(current_df, use_container_width=True, height=280, hide_index=True)
            st.caption("*Note: This is an approximation showing crowding impact. Full recalculation would also consider events, risk changes, etc.*")
    
    # Geographic mini-map showing all top 10 options
    st.write("**🌍 Geographic View of Options (Top 10):**")
    render_decision_map(all_dests[:10], decision['home_country_code'], chosen_code)
    
    # Factor breakdown bar chart for top 3 choices
    st.write("**Factor Breakdown (Top 3 Choices):**")
    
    factor_names = ['Attractiveness', 'Cost', 'Crowding', 'Risk', 'Distance', 'Memory', 'Event Bonus', 'Visa Friction']
    top_dests = all_dests[:10]  # Define top_dests for chart
    
    chart_data = []
    for dest in top_dests[:3]:
        is_chosen = dest['country_code'] == decision['chosen']
        chart_data.append({
            "Destination": f"{dest['country_name']}{' ✅' if is_chosen else ''}",
            "Attractiveness": dest['attractiveness'],
            "Cost": dest['cost'],
            "Crowding": dest['crowding'],
            "Risk": dest['risk'],
            "Distance": dest['distance'],
            "Memory": dest['memory'],
            "Event Bonus": dest['event_bonus'],
            "Visa Friction": dest['visa_friction'],
        })
    
    factor_df = pd.DataFrame(chart_data)
    factor_df = factor_df.set_index("Destination")
    
    fig = px.bar(
        factor_df,
        barmode="group",
        title="Utility Factor Contributions (positive = attractive, negative = repelling)",
        labels={"value": "Factor Contribution", "variable": "Factor"},
    )
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
    fig.update_traces(marker_line_width=0.5)
    
    # Add annotations for factors with no impact
    for i, factor in enumerate(factor_names):
        values = [chart_data[j][factor] for j in range(3)]
        if all(abs(v) < 0.01 for v in values):
            fig.add_annotation(
                x=i,
                text="No impact",
                showarrow=False,
                font=dict(size=9, color="gray"),
                yref="paper",
                y=0.02,
            )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show parameter values table for transparency
    st.write("**📊 Factor Parameters (Why Some Bars Are Empty):**")
    
    param_table = []
    for dest in top_dests[:3]:
        # Calculate normalized values from weighted contributions
        weights = SEGMENT_WEIGHTS.get(decision['segment'], SEGMENT_WEIGHTS['budget'])
        
        param_table.append({
            "Destination": dest['country_name'],
            "Attractiveness (norm)": f"{dest['attractiveness'] / weights['α']:.3f}",
            "→ Weighted": f"{dest['attractiveness']:+.3f}",
            "Cost (norm)": f"{abs(dest['cost']) / weights['β']:.3f}",
            "→ Weighted": f"{dest['cost']:+.3f}",
            "Crowding (norm)": f"{abs(dest['crowding']) / weights['γ']:.3f}",
            "→ Weighted": f"{dest['crowding']:+.3f}",
            "Risk (norm)": f"{abs(dest['risk']) / weights['δ']:.3f}",
            "→ Weighted": f"{dest['risk']:+.3f}",
            "Distance (norm)": f"{abs(dest['distance']) / weights['η']:.3f}",
            "→ Weighted": f"{dest['distance']:+.3f}",
            "Memory (norm)": f"{dest['memory'] / weights['ζ']:.3f}",
            "→ Weighted": f"{dest['memory']:+.3f}",
        })
    
    param_df = pd.DataFrame(param_table)
    st.dataframe(param_df, use_container_width=True, height=180, hide_index=True)
    
    st.caption("*Note: Factors with '0.000' normalized values have no impact on the decision (e.g., no crowding, no risk, no memory). The weighted contribution is the normalized value × segment weight.*")
    
    # Why chosen explanation
    if decision['chosen']:
        chosen_dest = next((d for d in decision['destinations'] if d['country_code'] == decision['chosen']), None)
        if chosen_dest:
            st.write("**Why this destination was chosen:**")
            
            # Find strongest positive and negative factors
            factors = {
                "Attractiveness": chosen_dest['attractiveness'],
                "Cost": chosen_dest['cost'],
                "Crowding": chosen_dest['crowding'],
                "Risk": chosen_dest['risk'],
                "Distance": chosen_dest['distance'],
                "Memory": chosen_dest['memory'],
                "Event Bonus": chosen_dest['event_bonus'],
                "Visa Friction": chosen_dest['visa_friction'],
            }
            
            positive_factors = {k: v for k, v in factors.items() if v > 0.01}
            negative_factors = {k: v for k, v in factors.items() if v < -0.01}
            
            col_pos, col_neg = st.columns(2)
            
            with col_pos:
                if positive_factors:
                    st.write("**✅ Positive Factors:**")
                    sorted_pos = sorted(positive_factors.items(), key=lambda x: x[1], reverse=True)
                    for factor, value in sorted_pos[:3]:
                        st.write(f"  • **{factor}**: +{value:.3f}")
                else:
                    st.write("No strong positive factors")
            
            with col_neg:
                if negative_factors:
                    st.write("**❌ Negative Factors:**")
                    sorted_neg = sorted(negative_factors.items(), key=lambda x: x[1])
                    for factor, value in sorted_neg[:3]:
                        st.write(f"  • **{factor}**: {value:.3f}")
                else:
                    st.write("No strong negative factors")


def calculate_gini_coefficient(sim):
    """
    Calculate Gini coefficient for utilization inequality across destinations.
    
    Returns:
        float: Gini coefficient (0 = perfect equality, 1 = perfect inequality)
    """
    # Get current utilization for all destinations
    utilizations = []
    for dest in sim.destinations.values():
        util = dest.get_crowding_ratio()
        if util > 0:  # Only include destinations with visitors
            utilizations.append(util)
    
    if len(utilizations) < 2:
        return 0.0
    
    # Sort utilizations
    utilizations = sorted(utilizations)
    n = len(utilizations)
    
    # Calculate Gini using the formula: G = (2 * sum(i * x_i) - (n+1) * sum(x_i)) / (n * sum(x_i))
    total = sum(utilizations)
    if total == 0:
        return 0.0
    
    indexed_sum = sum((i + 1) * util for i, util in enumerate(utilizations))
    gini = (2 * indexed_sum - (n + 1) * total) / (n * total)
    
    return min(max(gini, 0.0), 1.0)  # Clamp to [0, 1]


def render_capacity_dynamics(sim):
    """Render capacity utilization dynamics chart."""
    st.subheader("🏗️ Capacity Utilization Distribution")
    
    # Get current utilization for all destinations
    utilizations = []
    country_names = []
    
    for code, dest in sim.destinations.items():
        util = dest.get_crowding_ratio()
        if util > 0:  # Only include destinations with visitors
            utilizations.append(util * 100)  # Convert to percentage
            country_names.append(dest.country_name)
    
    if not utilizations:
        st.info("No destinations with visitors yet")
        return
    
    # Create histogram
    fig = px.histogram(
        x=utilizations,
        nbins=30,
        title="Distribution of Capacity Utilization Across Destinations",
        labels={"x": "Capacity Utilization (%)", "y": "Number of Destinations"},
    )
    
    # Add vertical lines for key thresholds
    fig.add_vline(x=100, line_dash="dash", line_color="orange", 
                  annotation_text="Full Capacity")
    fig.add_vline(x=50, line_dash="dot", line_color="green", 
                  annotation_text="50% Utilization")
    
    fig.update_layout(
        height=400,
        showlegend=True,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Utilization", f"{sum(utilizations)/len(utilizations):.1f}%")
    with col2:
        st.metric("Max Utilization", f"{max(utilizations):.1f}%")
    with col3:
        over_capacity = sum(1 for u in utilizations if u > 100)
        st.metric("Over Capacity", f"{over_capacity} destinations")
    with col4:
        under_50 = sum(1 for u in utilizations if u < 50)
        st.metric("Under 50%", f"{under_50} destinations")


def render_tfi_feedback_chart(sim):
    """Render TFI feedback loop chart."""
    st.subheader("🔄 Tourist Friction Index (TFI) Over Time")
    
    # Get TFI data for top destinations
    top_dest_codes = list(sim.destinations.keys())[:10]
    
    fig = go.Figure()
    
    for code in top_dest_codes:
        if code in sim.data_collector.dest_tfi:
            tfi_data = sim.data_collector.dest_tfi[code]
            if tfi_data:
                dest = sim.destinations.get(code)
                dest_name = dest.country_name if dest else code
                
                # Only show if TFI has varied
                if len(tfi_data) > 10 and max(tfi_data) - min(tfi_data) > 0.01:
                    fig.add_trace(go.Scatter(
                        y=tfi_data,
                        mode='lines',
                        name=dest_name,
                        line=dict(width=2),
                    ))
    
    # Add reference line for TFI=1 (neutral)
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray", 
                  annotation_text="Neutral TFI (no friction)")
    
    fig.update_layout(
        title="TFI Evolution (Values >1 = High Friction, <1 = Low Friction)",
        xaxis_title="Days Ago",
        yaxis_title="TFI Value",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Explanation
    st.caption("""
    **TFI (Tourist Friction Index)** represents the combined effect of crowding, risk, and policy barriers.
    - **TFI > 1**: High friction - tourists face barriers (overcrowding, high risk, strict policies)
    - **TFI = 1**: Neutral - normal conditions
    - **TFI < 1**: Low friction - favorable conditions attract more tourists
    
    Rising TFI creates a negative feedback loop that reduces arrivals, demonstrating emergent self-regulation.
    """)


def render_gini_chart(sim, gini_coefficient):
    """Render Gini coefficient chart for utilization inequality."""
    st.subheader("📊 Tourism Inequality (Gini Coefficient)")
    
    # Display current Gini
    gini_color = "green" if gini_coefficient < 0.3 else "orange" if gini_coefficient < 0.5 else "red"
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric(
            "Current Gini",
            f"{gini_coefficient:.3f}",
            help="0 = perfect equality (all destinations equally popular), 1 = perfect inequality (one destination has all tourists)"
        )
    
    with col2:
        # Interpretation
        if gini_coefficient < 0.3:
            st.success("**Low Inequality**: Tourism is well-distributed across destinations")
        elif gini_coefficient < 0.5:
            st.warning("**Moderate Inequality**: Some destinations are significantly more popular")
        else:
            st.error("**High Inequality**: Tourism is concentrated in a few popular destinations")
    
    # Create Lorenz curve data
    utilizations = []
    for dest in sim.destinations.values():
        util = dest.get_crowding_ratio()
        if util > 0:
            utilizations.append(util)
    
    if len(utilizations) >= 2:
        utilizations = sorted(utilizations)
        n = len(utilizations)
        total = sum(utilizations)
        
        # Calculate cumulative shares
        cumulative_pop = [(i + 1) / n for i in range(n)]
        cumulative_util = [sum(utilizations[:i+1]) / total for i in range(n)]
        
        # Perfect equality line
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[0] + cumulative_pop,
            y=[0] + cumulative_util,
            mode='lines',
            name='Actual Distribution',
            line=dict(color='blue', width=3),
        ))
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode='lines',
            name='Perfect Equality',
            line=dict(color='gray', dash='dash'),
        ))
        
        fig.update_layout(
            title="Lorenz Curve - Tourism Distribution",
            xaxis_title="Cumulative Share of Destinations",
            yaxis_title="Cumulative Share of Tourists",
            height=400,
            showlegend=True,
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Historical trend
    if len(sim.data_collector.global_active) > 30:
        st.write("**📈 Gini Trend (Last 90 Days):**")
        
        # Calculate rolling Gini (simplified - just show trend direction)
        st.caption("Gini coefficient tracks inequality in destination popularity. Rising Gini indicates increasing concentration.")


def render_event_impact_analysis(sim):
    """Render event impact analysis chart."""
    st.subheader("⚡ Negative Event Impact")
    
    # Check if any events are active
    active_events = [e for e in sim.unplanned_events if e.is_active(sim.current_date)]
    
    if not active_events:
        st.info("No active negative events. Use the sidebar to trigger events for impact analysis.")
        return
    
    for event in active_events:
        # Find affected destination
        affected_dest = sim.destinations.get(event.country_code)
        if not affected_dest:
            continue
        
        st.write(f"**Event: {event.event_type} in {affected_dest.country_name}**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Severity", event.severity.name)
        with col2:
            days_left = (event.end_date - sim.current_date).days
            st.metric("Days Remaining", max(0, days_left))
        with col3:
            current_tfi = affected_dest.tfi
            st.metric("Current TFI", f"{current_tfi:.2f}")
        with col4:
            current_visitors = affected_dest.get_current_visitors()
            st.metric("Current Visitors", f"{current_visitors:,}")
        
        # Show impact on arrivals over time
        if event.country_code in sim.data_collector.dest_visitors:
            visitors_data = sim.data_collector.dest_visitors[event.country_code]
            
            if len(visitors_data) > 10:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=visitors_data,
                    mode='lines',
                    name='Visitors',
                    line=dict(color='blue'),
                ))
                
                # Mark event start
                event_start_idx = len(visitors_data) - max(1, (event.end_date - event.start_date).days)
                fig.add_vrect(
                    x0=event_start_idx,
                    x1=len(visitors_data),
                    fillcolor="red",
                    opacity=0.2,
                    layer="below",
                    line_width=0,
                    annotation_text="Event Period",
                )
                
                fig.update_layout(
                    title=f"Impact on {affected_dest.country_name}",
                    xaxis_title="Days Ago",
                    yaxis_title="Number of Visitors",
                    height=300,
                    showlegend=False,
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.divider()


if __name__ == "__main__":
    main()
