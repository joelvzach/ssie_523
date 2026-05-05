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


def create_simulation(agent_count: int = 40000, start_date: datetime = None, sampled_agents: int = 100):
    """Create and initialize simulation with configured events.

    Args:
        agent_count: Number of tourist agents (default: 40,000)
        start_date: Simulation start date (default: January 1, 2026)
        sampled_agents: Number of agents to sample for visualization (default: 100)
    """
    if start_date is None:
        start_date = datetime(2026, 1, 1)
    
    with st.spinner(f"Initializing simulation with {agent_count:,} agents ({sampled_agents} sampled) starting {start_date.strftime('%B %d, %Y')}..."):
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
            "sampled_agents": sampled_agents,
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
                            "is_home": False,
                        }
                    )
            elif agent.state == "CHOOSING":
                # Show CHOOSING agents at home location with purple color (planning state)
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
                            "is_home": False,
                        }
                    )
            elif agent.state == "HOME":
                # Show HOME agents at home location with segment color outline, gray fill
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
                            "color": segment_colors.get(agent.segment, "#999999"),
                            "state": "HOME",
                            "is_home": True,  # Flag for hollow marker styling
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
        title=f"Global Tourism Map (colored by segment, faded=at home)",
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

    # Add traveling agents as scatter overlay with differentiated styling
    if len(agent_data) > 0:
        # Separate HOME agents (hollow) from TRAVELING/CHOOSING agents (solid)
        home_agents = agent_data[agent_data["is_home"] == True]
        traveling_agents = agent_data[agent_data["is_home"] != True]
        
        # Render TRAVELING/CHOOSING agents as solid colored circles
        if len(traveling_agents) > 0:
            fig.add_trace(
                go.Scattergeo(
                    lon=traveling_agents["longitude"],
                    lat=traveling_agents["latitude"],
                    mode="markers",
                    marker=dict(
                        size=6,
                        color=traveling_agents["color"],
                        symbol="circle",
                        line=dict(width=1, color="white"),
                    ),
                    text=traveling_agents.apply(
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
                    name="Active Agents",
                )
            )
        
        # Render HOME agents as smaller circles with segment color (at home location)
        if len(home_agents) > 0:
            fig.add_trace(
                go.Scattergeo(
                    lon=home_agents["longitude"],
                    lat=home_agents["latitude"],
                    mode="markers",
                    marker=dict(
                        size=4,  # Smaller for home agents
                        color=home_agents["color"],  # Segment color
                        symbol="circle",  # Same symbol, smaller size
                        opacity=0.5,  # Semi-transparent to indicate "at home"
                        line=dict(width=1, color="white"),
                    ),
                    text=home_agents.apply(
                        lambda row: (
                            f"Agent: {row['agent_id']}<br>"
                            f"Segment: {row['segment']}<br>"
                            f"State: {row['state']}<br>"
                            f"Location: {row['home_country']} (Home)<br>"
                            f"Days Until Next Trip: {row['days_remaining']}"
                        ),
                        axis=1,
                    ),
                    hoverinfo="text",
                    name="Home Agents",
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
    """Render time series chart of arrivals (global or country-specific) with dates."""
    if selected_country and selected_country != "Global":
        # Country-specific time series
        if selected_country in sim.data_collector.dest_visitors:
            country_arrivals = sim.data_collector.dest_visitors[selected_country]
            # Generate dates from simulation start date
            from datetime import timedelta
            start_date = sim.current_date - timedelta(days=len(country_arrivals))
            dates = [(start_date + timedelta(days=i)).strftime("%b %d") for i in range(len(country_arrivals))]
            
            df = pd.DataFrame(
                {
                    "Date": dates,
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

        from datetime import timedelta
        start_date = sim.current_date - timedelta(days=len(arrivals))
        dates = [(start_date + timedelta(days=i)).strftime("%b %d") for i in range(len(arrivals))]
        
        df = pd.DataFrame(
            {
                "Date": dates,
                "Arrivals": arrivals,
            }
        )
        title = "🌍 Global - Daily Arrivals"

    fig = px.line(
        df,
        x="Date",
        y="Arrivals",
        title=title,
        markers=False,
    )

    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="Date",
        yaxis_title="Number of Arrivals",
        xaxis_tickangle=-45,
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


def render_visitor_origin_map(sim, country_code):
    """Render world map showing visitor origins with highlighted countries."""
    # Get trip records for this destination
    trips = [
        t for t in sim.data_collector.trip_records
        if t['destination'] == country_code
    ]
    
    if not trips:
        st.info("No visitor data available yet.")
        return
    
    # Filter to last 90 days
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
    
    # Build map data with coordinates
    origin_data = []
    for code, count in origin_counts.items():
        origin_dest = sim.destinations.get(code)
        if origin_dest:
            origin_data.append({
                'country': origin_dest.country_name,
                'code': code,
                'visitors': count,
                'lat': origin_dest.latitude,
                'lon': origin_dest.longitude,
            })
    
    if not origin_data:
        st.info("Could not map visitor origins.")
        return
    
    # Sort by visitors for color scale
    origin_data.sort(key=lambda x: x['visitors'], reverse=True)
    
    # Create map
    df = pd.DataFrame(origin_data)
    
    fig = go.Figure()
    
    # Base world map
    fig.add_trace(go.Choropleth(
        locations=df['code'],
        z=df['visitors'],
        locationmode='ISO-3',  # Fixed: use 'ISO-3' not 'country codes'
        colorscale='Blues',
        colorbar_title='Visitors',
        hovertemplate='%{location}: %{z} visitors<extra></extra>',
    ))
    
    # Highlight destination country
    dest = sim.destinations.get(country_code)
    if dest:
        fig.add_trace(go.Choropleth(
            locations=[country_code],
            z=[max(df['visitors']) * 1.5],  # Make it stand out
            locationmode='ISO-3',  # Fixed: use 'ISO-3'
            colorscale=[[0, 'red'], [1, 'red']],  # Red highlight
            showslegend=True,
            name='Destination',
            hovertemplate=f'{dest.country_name}: Destination<extra></extra>',
        ))
    
    fig.update_layout(
        title=f"Visitor Origins Map for {dest.country_name if dest else country_code}",
        geo=dict(
            showframe=True,
            showcoastlines=True,
            projection_type='equirectangular',
        ),
        height=500,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show summary statistics
    st.write(f"**📊 Visitor Origin Summary (Last 90 Days):**")
    total_visitors = sum(origin_counts.values())
    unique_origins = len(origin_counts)
    
    col_sum1, col_sum2, col_sum3 = st.columns(3)
    with col_sum1:
        st.metric("Total Visitors", f"{total_visitors:,}")
    with col_sum2:
        st.metric("Countries of Origin", f"{unique_origins}")
    with col_sum3:
        top_origin = origin_counts.most_common(1)[0]
        top_name = sim.destinations.get(top_origin[0])
        st.metric("Top Origin", f"{top_name.country_name if top_name else top_origin[0]} ({top_origin[1]})")


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

            # Sampled Agents for Visualization
            sampled_agents = st.slider(
                "Agents to Sample for Visualization",
                min_value=50,
                max_value=500,
                value=100,
                step=50,
                help="Number of agents to track individually for detailed visualization. "
                "More sampled agents = more detailed agent dashboard, but slightly slower rendering. "
                "100 agents recommended for most use cases.",
                key="sampled_agents_slider",
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
                    f"Initialize button clicked with {agent_count:,} agents ({sampled_agents} sampled) starting {start_date}"
                ),
                key="initialize_simulation_button",
            ):
                create_simulation(agent_count, start_date, sampled_agents)
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
        
        # Agent type legend
        st.divider()
        st.subheader("🎨 Agent Types")
        
        col_leg1, col_leg2, col_leg3, col_leg4 = st.columns(4)
        with col_leg1:
            st.markdown("""
            **🔵 Budget (30%)**
            - Cost-sensitive
            - Short-haul preference
            - 1-2 trips/year
            """)
        with col_leg2:
            st.markdown("""
            **🟠 Luxury (20%)**
            - Quality-focused
            - Less price-sensitive
            - 2-3 trips/year
            """)
        with col_leg3:
            st.markdown("""
            **🟢 Adventure (25%)**
            - Risk-tolerant
            - Off-the-beaten-path
            - 1-2 trips/year
            """)
        with col_leg4:
            st.markdown("""
            **🔴 Family (25%)**
            - Safety-conscious
            - Strong distance penalty
            - 1 trip/year
            """)
        
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
            
            # Add visitor origin map
            st.divider()
            st.subheader("🌍 Visitor Origins Map")
            render_visitor_origin_map(sim, selected_country)
        else:
            # Show overview with time series and top destinations
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
        ### Complexity Science Concepts
        
        This simulation demonstrates key concepts from complexity science:
        **Power Laws**, **Heterogeneity**, **Emergence**, **Feedback Loops**, **Path Dependence**, and **Resilience**.
        """)
        
        if not st.session_state.running:
            # Calculate complexity metrics
            gini_coefficient = calculate_gini_coefficient(sim)
            power_law_params = fit_power_law(sim)
            
            # Create analytics tabs organized by complexity concept
            tab_power, tab_hetero, tab_feedback, tab_path, tab_resilience, tab_emergence = st.tabs([
                "⚡ Power Law",
                "🎭 Heterogeneity", 
                "🔄 Feedback Loops",
                "📊 Path Dependence",
                "🛡️ Resilience",
                "🌟 Emergence"
            ])
            
            with tab_power:
                render_power_law_chart(sim, power_law_params)
            
            with tab_hetero:
                render_heterogeneity_chart(sim)
            
            with tab_feedback:
                render_feedback_loop_chart(sim)
            
            with tab_path:
                render_path_dependence_chart(sim, gini_coefficient)
            
            with tab_resilience:
                render_resilience_chart(sim)
            
            with tab_emergence:
                render_emergence_chart(sim)
            
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
        st.info("⬅️ Use the sidebar to trigger negative events and configure simulation parameters")


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
                elif agent.state == "HOME":
                    current_dest_display = "-"
                elif agent.current_destination:
                    # Convert country code to full name
                    dest = sim.destinations.get(agent.current_destination)
                    if dest:
                        current_dest_display = f"{dest.country_name} ({agent.current_destination})"
                    else:
                        current_dest_display = agent.current_destination
                else:
                    current_dest_display = "-"

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
            # Main table with all agents
            st.dataframe(df, use_container_width=True, height=400, hide_index=True)

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
                # Trip frequency by segment
                trip_freq = {}
                for segment in ['Budget', 'Luxury', 'Adventure', 'Family']:
                    segment_agents = [a for a in sim.agents if a.segment == segment.lower() and a.agent_id in sim.sampled_agent_ids]
                    if segment_agents:
                        # Calculate average trips per agent (based on trips in history)
                        total_trips = sum(len([t for t in sim.data_collector.trip_records if t['segment'] == segment.lower()]) for _ in range(1))
                        avg_trips = total_trips / len(segment_agents) * (365 / max(1, sim.tick))
                        trip_freq[segment] = avg_trips
                
                if trip_freq:
                    fig_freq = px.bar(
                        x=list(trip_freq.keys()),
                        y=list(trip_freq.values()),
                        title="Avg Trips/Year by Segment",
                        color=list(trip_freq.keys()),
                        color_discrete_map={
                            "Budget": "#1f77b4",
                            "Luxury": "#ff7f0e",
                            "Adventure": "#2ca02c",
                            "Family": "#d62728",
                        },
                    )
                    fig_freq.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig_freq, use_container_width=True)

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
            
            selected_agent = st.selectbox(
                "Agent:",
                options=sorted(df["Name"].unique()),
                help="Choose an agent to view their complete journey trajectory",
                key="filter_agent_selectbox"
            )
            
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
                
                # Get trip records for this agent (includes decision data)
                agent_trips = [
                    t for t in sim.data_collector.trip_records 
                    if t['agent_id'] == selected_agent and t.get('decision_data')
                ]
                
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
                    
                    # Create journey dataframe with clickable rows
                    journey_data = []
                    for idx, (start_tick, end_tick, dest_code) in enumerate(trips):
                        dest = sim.destinations.get(dest_code)
                        dest_name = dest.country_name if dest else dest_code
                        duration = end_tick - start_tick + 1
                        
                        # Check if this trip has decision data
                        has_decision = any(
                            abs(t['arrival_tick'] - start_tick) <= 1  # Match arrival tick
                            for t in agent_trips
                        )
                        
                        journey_data.append({
                            "Trip #": idx + 1,
                            "Day": f"{start_tick} → {end_tick}",
                            "Destination": f"{dest_name} ({dest_code})",
                            "Duration": f"{duration}d",
                            "View Decision": "🔍 Click below" if has_decision else "-",
                        })
                    
                    journey_df = pd.DataFrame(journey_data)
                    st.dataframe(journey_df, use_container_width=True, height=300, hide_index=True)
                    
                    # Trip selector for viewing decisions
                    if agent_trips:
                        st.write("**🔍 View Past Decisions:**")
                        
                        # Build trip options
                        trip_options = {}
                        for trip in agent_trips:
                            dest = sim.destinations.get(trip['destination'])
                            dest_name = dest.country_name if dest else trip['destination']
                            label = f"Trip to {dest_name} (Day {trip['arrival_tick']})"
                            trip_options[label] = trip
                        
                        selected_trip_label = st.selectbox(
                            "Select a trip to view its decision breakdown:",
                            options=list(trip_options.keys()),
                            help="View the factor breakdown that led to this destination choice"
                        )
                        
                        if selected_trip_label:
                            selected_trip = trip_options[selected_trip_label]
                            decision_data = selected_trip.get('decision_data')
                            
                            if decision_data:
                                st.write(f"**Decision Details for {selected_trip_label}:**")
                                render_decision_breakdown(decision_data, sim)
                    
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
    
    # Enhanced table with detailed factor breakdown
    table_data = []
    for i, dest in enumerate(table_dests):
        is_chosen = dest['country_code'] == decision['chosen']
        rank = all_dests.index(dest) + 1
        
        # Get detailed factors
        weights = SEGMENT_WEIGHTS.get(decision['segment'], SEGMENT_WEIGHTS['budget'])
        
        table_data.append({
            "Rank": rank,
            "Destination": f"{dest['country_name']} ({dest['country_code']})",
            "Utility": f"{dest['utility']:.3f}",
            "Probability": f"{dest['probability']:.2%}",
            "Attractiveness": f"+{dest['attractiveness']:.3f}",
            "Distance": f"{dest['distance']:.3f}",
            "Crowding": f"{dest['crowding']:.3f}",
            "Chosen": "✅ WINNER" if is_chosen else "",
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, height=350, hide_index=True)
    
    # Winner explanation
    if decision['chosen']:
        chosen_data = next((d for d in all_dests if d['country_code'] == decision['chosen']), None)
        if chosen_data:
            st.divider()
            st.write("**🏆 Why {0} Won:**".format(chosen_data['country_name']))
            
            # Find strongest positive factors
            factors = {
                "Attractiveness": chosen_data['attractiveness'],
                "Distance": chosen_data['distance'],
                "Crowding": chosen_data['crowding'],
                "Risk": chosen_data['risk'],
                "Memory": chosen_data['memory'],
                "Event Bonus": chosen_data['event_bonus'],
            }
            
            positive_factors = [(k, v) for k, v in factors.items() if v > 0.01]
            positive_factors.sort(key=lambda x: x[1], reverse=True)
            
            if positive_factors:
                st.write("**Key Advantages:**")
                for factor, value in positive_factors[:3]:
                    st.write(f"  • **{factor}**: +{value:.3f}")
            
            # Compare to #2 choice
            runner_up = next((d for d in all_dests if d['country_code'] != decision['chosen']), None)
            if runner_up:
                utility_diff = chosen_data['utility'] - runner_up['utility']
                prob_diff = chosen_data['probability'] - runner_up['probability']
                
                st.write(f"\n**vs. #{2} ({runner_up['country_name']}):**")
                st.write(f"  • Utility advantage: +{utility_diff:.3f}")
                st.write(f"  • Probability advantage: +{prob_diff:.2%}")
    
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
    
    # Check if any events exist (active or past)
    all_events = sim.unplanned_events.events
    
    if not all_events:
        st.info("""
        **No negative events triggered yet.**
        
        To see resilience analysis:
        1. Go to sidebar → '⚠️ Trigger Negative Event'
        2. Select a country, event type, severity, and duration
        3. Click '⚡ Trigger Event'
        4. Run simulation for 30+ days to see impact
        5. Return to this tab to see resilience metrics
        
        **What you'll see:**
        - Visitor drop during event
        - Recovery rate after event ends
        - Substitution effect (where tourists went instead)
        """)
        return
    
    # Show both active and past events
    active_events = [e for e in all_events if e.is_active(sim.current_date)]
    past_events = [e for e in all_events if not e.is_active(sim.current_date)]
    
    for event in active_events:
        # Find affected destination
        affected_dest = sim.destinations.get(event.country_code)
        if not affected_dest:
            continue
        
        st.write(f"**Event: {event.event_type.replace('_', ' ').title()} in {affected_dest.country_name}**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Severity", f"{event.severity:.0%}")
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
                    line=dict(color='blue', width=2),
                ))
                
                # Calculate event period indices relative to data length
                total_days = len(visitors_data)
                days_since_start = (sim.current_date - event.start_date).days
                event_duration = (event.end_date - event.start_date).days
                
                # Event started X days ago from current data
                event_start_idx = max(0, total_days - days_since_start)
                event_end_idx = min(total_days, event_start_idx + event_duration)
                
                # Mark event period
                if event_start_idx < total_days:
                    fig.add_vrect(
                        x0=event_start_idx,
                        x1=min(event_end_idx, total_days),
                        fillcolor="red",
                        opacity=0.25,
                        layer="below",
                        line_width=0,
                        annotation_text="Event Period",
                    )
                
                # Mark event start with vertical line
                if event_start_idx < total_days:
                    fig.add_vline(
                        x=event_start_idx,
                        line_dash="dash",
                        line_color="red",
                        line_width=2,
                        annotation_text=f"Event Started ({event.start_date.strftime('%b %d')})",
                    )
                
                fig.update_layout(
                    title=f"Impact on {affected_dest.country_name} - Daily Visitors",
                    xaxis_title=f"Day (0 = {sim.current_date - timedelta(days=total_days-1):%b %d})",
                    yaxis_title="Number of Visitors",
                    height=350,
                    showlegend=False,
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show statistics
                pre_event = visitors_data[:event_start_idx] if event_start_idx > 0 else []
                during_event = visitors_data[event_start_idx:event_end_idx] if event_start_idx < total_days else []
                
                if pre_event and during_event:
                    avg_pre = sum(pre_event) / len(pre_event)
                    avg_during = sum(during_event) / len(during_event) if during_event else 0
                    impact_pct = ((avg_pre - avg_during) / avg_pre * 100) if avg_pre > 0 else 0
                    
                    col_imp1, col_imp2, col_imp3 = st.columns(3)
                    with col_imp1:
                        st.metric("Avg Before Event", f"{avg_pre:.1f}")
                    with col_imp2:
                        st.metric("Avg During Event", f"{avg_during:.1f}")
                    with col_imp3:
                        impact_emoji = "📉" if impact_pct > 0 else "📈"
                        st.metric("Impact", f"{impact_emoji} {impact_pct:.1f}%")
        
        st.divider()


def fit_power_law(sim):
    """
    Fit power law to destination popularity distribution using historical arrival data.
    
    Returns:
        dict: Power law parameters (alpha, r_squared)
    """
    import numpy as np
    from scipy import stats
    
    # Use cumulative arrivals over time for better power law fit
    # This smooths out temporary fluctuations
    cumulative_visitors = {}
    for code, dest in sim.destinations.items():
        arrivals_history = sim.data_collector.dest_visitors.get(code, [])
        if arrivals_history:
            # Sum all arrivals (more stable than current snapshot)
            cumulative_visitors[code] = sum(arrivals_history)
    
    visitors = list(cumulative_visitors.values())
    
    if len(visitors) < 10 or max(visitors) == 0:
        return None
    
    # Filter out zeros
    visitors = [v for v in visitors if v > 0]
    
    if len(visitors) < 10:
        return None
    
    # Sort by rank (descending)
    visitors = sorted(visitors, reverse=True)
    
    # Log-transform for power law fit: log(rank) vs log(value)
    ranks = np.arange(1, len(visitors) + 1)
    log_ranks = np.log(ranks)
    log_values = np.log(visitors)
    
    # Fit linear regression (power law: value ~ rank^(-alpha))
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_ranks, log_values)
    
    # Power law exponent (alpha = -slope)
    alpha = -slope
    r_squared = r_value ** 2
    
    return {
        'alpha': alpha,
        'r_squared': r_squared,
        'ranks': ranks,
        'visitors': visitors,
        'slope': slope,
        'intercept': intercept,
    }


def render_power_law_chart(sim, power_law_params):
    """Render power law distribution chart with population comparison."""
    st.subheader("⚡ Power Law in Destination Popularity")
    
    if not power_law_params:
        st.info("Not enough data yet to fit power law (need destinations with visitors)")
        return
    
    # Create two-column layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Create rank-frequency plot
        fig = go.Figure()
        
        # Actual data
        fig.add_trace(go.Scatter(
            x=power_law_params['ranks'],
            y=power_law_params['visitors'],
            mode='markers',
            name='Actual Data',
            marker=dict(size=8, color='blue', opacity=0.6),
        ))
        
        # Power law fit line
        import numpy as np
        fit_values = np.exp(power_law_params['intercept']) * (power_law_params['ranks'] ** power_law_params['slope'])
        fig.add_trace(go.Scatter(
            x=power_law_params['ranks'],
            y=fit_values,
            mode='lines',
            name=f'Power Law Fit (α={power_law_params["alpha"]:.2f})',
            line=dict(color='red', width=3),
        ))
        
        fig.update_layout(
            title="Tourism Popularity (Log-Log Scale)",
            xaxis_title="Rank (1 = Most Popular)",
            yaxis_title="Number of Visitors",
            xaxis_type="log",
            yaxis_type="log",
            height=400,
            showlegend=True,
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top countries by population bar chart
        # Load population data from file
        from pathlib import Path
        from simulation.data.loaders import load_population_data
        
        pop_lookup = load_population_data(Path("/Users/joelvzach/Code/ssie_523/data/derived"))
        
        pop_data = []
        for code, dest in sim.destinations.items():
            population = pop_lookup.get(code, 0)
            if population > 0:
                pop_data.append({
                    'country': dest.country_name,
                    'population': population,
                    'visitors': dest.get_current_visitors(),
                })
        
        if pop_data:
            # Sort by population and take top 15
            pop_data = sorted(pop_data, key=lambda x: x['population'], reverse=True)[:15]
            pop_df = pd.DataFrame(pop_data)
            
            fig_pop = px.bar(
                pop_df,
                x='country',
                y='population',
                title="Top 15 Countries by Population",
                labels={'country': 'Country', 'population': 'Population'},
            )
            fig_pop.update_layout(
                height=400,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_pop, use_container_width=True)
        else:
            st.info("Population data not available - check data/derived/country_population.csv")
    
    # Interpretation
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Power Law Exponent (α)", f"{power_law_params['alpha']:.3f}",
                  help="Typical range: 0.5-2.0. Lower = more unequal (winner-take-all)")
    with col_m2:
        r2 = power_law_params['r_squared']
        fit_quality = "Excellent" if r2 > 0.9 else "Good" if r2 > 0.7 else "Moderate" if r2 > 0.5 else "Weak"
        st.metric("R² (Fit Quality)", f"{r2:.3f}",
                  help=f"{fit_quality} fit - measures how well power law explains the data")
    
    st.caption("""
    **Power Law Interpretation**: A few destinations attract most tourists (winner-take-all dynamics).
    This emerges from preferential attachment: popular destinations become more popular through memory effects
    and positive feedback loops, while less popular ones struggle to attract visitors.
    
    **Note**: Tourism popularity does NOT correlate strongly with population - small countries (e.g., UAE, Croatia)
    can be tourism leaders through targeted investment and natural/cultural attractions.
    """)


def render_heterogeneity_chart(sim):
    """Render segment heterogeneity chart."""
    st.subheader("🎭 Segment Heterogeneity")
    
    # Get arrivals by segment over time
    if not sim.data_collector.segment_arrivals.get('budget'):
        st.info("Not enough data yet to show segment heterogeneity")
        return
    
    fig = go.Figure()
    
    segment_colors = {
        'budget': '#1f77b4',
        'luxury': '#ff7f0e',
        'adventure': '#2ca02c',
        'family': '#d62728',
    }
    
    # Plot arrivals over time for each segment
    for segment, color in segment_colors.items():
        arrivals = sim.data_collector.segment_arrivals.get(segment, [])
        if arrivals:
            # Calculate rolling average for smoother visualization
            window = min(30, len(arrivals) // 4) if len(arrivals) > 4 else 1
            if window > 1:
                smoothed = np.convolve(arrivals, np.ones(window)/window, mode='valid')
                days = list(range(len(arrivals) - window + 1))
            else:
                smoothed = arrivals
                days = list(range(len(arrivals)))
            
            fig.add_trace(go.Scatter(
                x=days,
                y=smoothed,
                mode='lines',
                name=segment.capitalize(),
                line=dict(color=color, width=2),
            ))
    
    fig.update_layout(
        title="Tourism Arrivals by Segment (30-day Rolling Average)",
        xaxis_title="Days Ago",
        yaxis_title="Arrivals",
        height=400,
        showlegend=True,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Segment divergence metric
    st.write("**📊 Segment Divergence Analysis:**")
    
    # Calculate coefficient of variation between segments
    recent_arrivals = []
    for segment in ['budget', 'luxury', 'adventure', 'family']:
        arrivals = sim.data_collector.segment_arrivals.get(segment, [])
        if arrivals and len(arrivals) >= 7:
            recent_arrivals.append(np.mean(arrivals[-7:]))
    
    if len(recent_arrivals) == 4:
        cv = np.std(recent_arrivals) / np.mean(recent_arrivals)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Segment CV (Heterogeneity)", f"{cv:.3f}",
                      help="Higher = more divergent segment behaviors")
        with col2:
            interpretation = "High" if cv > 0.5 else "Moderate" if cv > 0.2 else "Low"
            st.metric("Behavioral Divergence", interpretation)
    
    st.caption("""
    **Heterogeneity**: Different traveler segments exhibit distinct behaviors due to varying
    preferences (budget sensitivity, luxury preference, risk tolerance). This diversity
    creates system resilience through distributed response patterns.
    """)


def render_feedback_loop_chart(sim):
    """Render TFI feedback loop (arrivals vs friction)."""
    st.subheader("🔄 Negative Feedback Loop: TFI → Arrivals")
    
    # Check if we have enough data
    if not sim.data_collector.dest_tfi or not sim.data_collector.dest_visitors:
        st.info("""
        **Data Requirements for Feedback Loop Analysis:**
        
        This chart needs at least 30 days of simulation data to show the TFI-Arrivals relationship.
        
        **What you'll see:**
        - Scatter plot: Each point = one day for one destination
        - X-axis: TFI (Tourist Friction Index) - higher = more crowding/barriers
        - Y-axis: Daily arrivals
        - Trend line: Negative slope = self-regulating system
        
        **Expected pattern:** Downward-sloping trend (high TFI → fewer arrivals)
        """)
        return
    
    # Get destinations with sufficient TFI variation
    feedback_data = []
    
    for code, dest in sim.destinations.items():
        tfi_history = sim.data_collector.dest_tfi.get(code, [])
        arrivals_history = sim.data_collector.dest_visitors.get(code, [])
        
        if len(tfi_history) > 30 and len(arrivals_history) > 30:
            # Use recent data
            for i in range(len(tfi_history)):
                feedback_data.append({
                    'TFI': tfi_history[i],
                    'Arrivals': arrivals_history[i],
                    'Destination': dest.country_name,
                })
    
    if not feedback_data:
        st.info(f"""
        **Insufficient Data Yet**
        
        Current simulation: {sim.tick} days
        Minimum required: 30 days with TFI variation
        
        **Tips to see feedback loops faster:**
        1. Run simulation for 60+ days
        2. Trigger negative events (sidebar) to create TFI spikes
        3. Focus on popular destinations (France, Spain, USA)
        """)
        return
    
    df_feedback = pd.DataFrame(feedback_data)
    
    # Create scatter plot with time arrows
    fig = px.scatter(
        df_feedback,
        x='TFI',
        y='Arrivals',
        color='Destination',
        opacity=0.5,
        title="TFI vs Arrivals (Negative Feedback: Higher TFI → Fewer Arrivals)",
        labels={'TFI': 'Tourist Friction Index', 'Arrivals': 'Daily Arrivals'},
    )
    
    # Add trend line
    import numpy as np
    from scipy import stats
    
    if len(df_feedback) > 10:
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df_feedback['TFI'], df_feedback['Arrivals']
        )
        
        x_range = np.linspace(df_feedback['TFI'].min(), df_feedback['TFI'].max(), 100)
        y_fit = slope * x_range + intercept
        
        fig.add_trace(go.Scatter(
            x=x_range,
            y=y_fit,
            mode='lines',
            name=f'Trend (r={r_value:.2f})',
            line=dict(color='red', width=2, dash='dash'),
        ))
    
    fig.update_layout(
        height=500,
        showlegend=True,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Feedback strength
    if len(df_feedback) > 10:
        correlation = df_feedback['TFI'].corr(df_feedback['Arrivals'])
        feedback_strength = "Strong Negative" if correlation < -0.5 else "Moderate Negative" if correlation < -0.2 else "Weak" if correlation < 0 else "Positive (unusual)"
        
        col_fb1, col_fb2 = st.columns(2)
        with col_fb1:
            st.metric("TFI-Arrivals Correlation", f"{correlation:.3f}",
                      help=f"{feedback_strength} feedback - negative correlation shows self-regulation")
        with col_fb2:
            st.metric("Feedback Type", feedback_strength)
    
    st.caption("""
    **Negative Feedback Loop**: As destinations become crowded (high TFI), they become less
    attractive, causing tourists to choose alternatives. This self-regulating mechanism
    prevents runaway overcrowding and demonstrates emergent homeostasis.
    
    **Causal Chain**: Crowding → Higher TFI → Lower Utility → Fewer Arrivals → Reduced Crowding
    """)


def render_path_dependence_chart(sim, gini_coefficient):
    """Render path dependence via Gini coefficient trend."""
    st.subheader("📊 Path Dependence: Rich-Get-Richer Dynamics")
    
    # Calculate historical Gini from destination data
    gini_history = []
    
    # Sample points in time (every 10 days for efficiency)
    max_days = len(sim.data_collector.global_arrivals)
    if max_days < 20:
        st.info("Not enough historical data yet")
        return
    
    for day in range(0, max_days, max(1, max_days // 50)):  # Sample 50 points
        # Reconstruct utilization at this point in time
        utilizations_at_day = []
        for code, dest in sim.destinations.items():
            util_history = sim.data_collector.dest_capacity_util.get(code, [])
            if day < len(util_history):
                util = util_history[day]
                if util > 0:
                    utilizations_at_day.append(util)
        
        if len(utilizations_at_day) >= 2:
            # Calculate Gini for this day
            utilizations_at_day = sorted(utilizations_at_day)
            n = len(utilizations_at_day)
            total = sum(utilizations_at_day)
            if total > 0:
                indexed_sum = sum((i + 1) * util for i, util in enumerate(utilizations_at_day))
                gini = (2 * indexed_sum - (n + 1) * total) / (n * total)
                gini_history.append({'Day': day, 'Gini': min(max(gini, 0), 1)})
    
    if not gini_history:
        st.info("Could not calculate historical Gini")
        return
    
    df_gini = pd.DataFrame(gini_history)
    
    # Plot Gini trend
    fig = px.line(
        df_gini,
        x='Day',
        y='Gini',
        title="Gini Coefficient Over Time (Rising = Increasing Inequality)",
        labels={'Day': 'Simulation Day', 'Gini': 'Gini Coefficient'},
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
    )
    
    # Add reference lines
    fig.add_hrect(y0=0, y1=0.3, fillcolor="green", opacity=0.1, annotation_text="Low Inequality")
    fig.add_hrect(y0=0.3, y1=0.5, fillcolor="orange", opacity=0.1, annotation_text="Moderate")
    fig.add_hrect(y0=0.5, y1=1, fillcolor="red", opacity=0.1, annotation_text="High Inequality")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Trend analysis
    if len(df_gini) > 10:
        first_half = df_gini.head(len(df_gini)//2)['Gini'].mean()
        second_half = df_gini.tail(len(df_gini)//2)['Gini'].mean()
        trend = "Increasing" if second_half > first_half * 1.05 else "Stable" if second_half > first_half * 0.95 else "Decreasing"
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Gini", f"{gini_coefficient:.3f}")
        with col2:
            st.metric("Historical Trend", trend)
        with col3:
            st.metric("Early Gini", f"{first_half:.3f}",
                      help="Gini from first half of simulation")
    
    st.caption("""
    **Path Dependence**: Early advantages compound over time. Destinations that attract
    tourists early gain memory bonuses, making them more attractive later. This creates
    a "rich-get-richer" dynamic where initial conditions determine long-term outcomes.
    Rising Gini coefficient indicates increasing concentration and lock-in effects.
    """)


def render_resilience_chart(sim):
    """Render resilience analysis (recovery from shocks)."""
    st.subheader("🛡️ System Resilience")
    
    # Check for historical events
    if not hasattr(sim, 'unplanned_events') or not sim.unplanned_events.events:
        st.info("No negative events have occurred yet. Trigger an event from the sidebar to analyze resilience.")
        return
    
    # Find past (completed) events
    past_events = [e for e in sim.unplanned_events.events 
                   if e.end_date < sim.current_date and (e.start_date - sim.current_date).days > -90]
    
    if not past_events:
        st.info("No recent events to analyze. Events need to complete before resilience can be measured.")
        return
    
    for event in past_events[:3]:  # Show up to 3 events
        affected_dest = sim.destinations.get(event.country_code)
        if not affected_dest:
            continue
        
        st.write(f"**Event: {event.event_type} in {affected_dest.country_name}**")
        
        # Get visitor data around event
        visitors_data = sim.data_collector.dest_visitors.get(event.country_code, [])
        if len(visitors_data) < 30:
            continue
        
        # Find event indices
        days_before = 30
        days_after = min(30, len(visitors_data) - 1)
        
        # Estimate event center (when impact was strongest)
        event_center = len(visitors_data) - days_after
        
        # Calculate pre-event baseline and post-event recovery
        pre_event = visitors_data[max(0, event_center-days_before):event_center]
        post_event = visitors_data[event_center:min(len(visitors_data), event_center+days_after)]
        
        if not pre_event or not post_event:
            continue
        
        baseline = np.mean(pre_event) if pre_event else 0
        min_impact = min(post_event) if post_event else 0
        current = post_event[-1] if post_event else 0
        
        # Calculate resilience metrics
        impact_depth = (baseline - min_impact) / baseline if baseline > 0 else 0
        recovery_rate = (current - min_impact) / (baseline - min_impact) if baseline > min_impact else 1.0
        
        # Plot
        fig = go.Figure()
        
        x_pre = list(range(event_center - len(pre_event), event_center))
        x_post = list(range(event_center, event_center + len(post_event)))
        
        fig.add_trace(go.Scatter(
            x=x_pre,
            y=pre_event,
            mode='lines',
            name='Pre-Event',
            line=dict(color='green'),
        ))
        
        fig.add_trace(go.Scatter(
            x=x_post,
            y=post_event,
            mode='lines',
            name='Recovery',
            line=dict(color='blue'),
        ))
        
        # Mark event
        fig.add_vline(x=event_center, line_dash='dash', line_color='red', 
                      annotation_text='Event')
        
        fig.update_layout(
            title=f"Impact & Recovery (Baseline: {baseline:.0f} visitors/day)",
            xaxis_title=f"Days Relative to Event (0 = Event)",
            yaxis_title="Daily Visitors",
            height=300,
            showlegend=True,
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Impact Depth", f"{impact_depth:.1%}",
                      help="Percentage drop from baseline")
        with col2:
            st.metric("Recovery Rate", f"{recovery_rate:.1%}",
                      help="How much of lost tourism recovered")
        with col3:
            resilience = "High" if recovery_rate > 0.7 else "Moderate" if recovery_rate > 0.4 else "Low"
            st.metric("Resilience", resilience)
        
        st.divider()
    
    st.caption("""
    **Resilience**: The system's ability to absorb shocks and recover. High resilience
    indicates distributed tourism (alternatives available), while low resilience suggests
    over-dependence on specific destinations.
    """)


def render_emergence_chart(sim):
    """Render emergence (spatial clustering, self-organization)."""
    st.subheader("🌟 Emergent Spatial Patterns")
    
    # Create spatial clustering visualization
    # Group destinations by continent using centroid region data
    from collections import defaultdict
    
    # Load region mapping from centroids
    from pathlib import Path
    from simulation.data.loaders import load_centroids
    project_root = Path("/Users/joelvzach/Code/ssie_523")
    centroids = load_centroids(project_root / "data" / "derived")
    
    continent_visitors = defaultdict(int)
    continent_destinations = defaultdict(int)
    continent_countries = defaultdict(list)
    
    for code, dest in sim.destinations.items():
        visitors = dest.get_current_visitors()
        
        # Get continent from centroids
        centroid_info = centroids.get(code, {})
        continent = centroid_info.get('region', 'Unknown')
        
        # Map region names to continent names
        continent_mapping = {
            'Americas': 'Americas',
            'Europe': 'Europe',
            'Asia': 'Asia',
            'Africa': 'Africa',
            'Oceania': 'Oceania',
            'Unknown': 'Unknown',
        }
        continent = continent_mapping.get(continent, continent)
        
        if visitors > 0:
            continent_visitors[continent] += visitors
            continent_destinations[continent] += 1
            continent_countries[continent].append(dest.country_name)
    
    # Filter out Unknown if we have other continents
    if 'Unknown' in continent_visitors and len(continent_visitors) > 1:
        del continent_visitors['Unknown']
        del continent_destinations['Unknown']
        del continent_countries['Unknown']
    
    if not continent_visitors:
        st.info("""
        **Not enough data yet to show emergent patterns**
        
        Run the simulation for more days to see tourism patterns emerge.
        
        **What you'll see:**
        - Treemap: Tourism concentration by continent
        - HHI: Concentration index (0-1, higher = more concentrated)
        - Tourism corridors: Most-traveled origin→destination pairs
        """)
        return
    
    # Create two-column layout
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Create treemap of tourism concentration
        fig = px.treemap(
            names=list(continent_visitors.keys()),
            parents=[''] * len(continent_visitors),
            values=list(continent_visitors.values()),
            title="Tourism Concentration by Continent",
            color=[continent_visitors[c] / max(1, continent_destinations[c]) for c in continent_visitors.keys()],
            color_continuous_scale='RdYlGn',
        )
        
        fig.update_layout(
            height=450,
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        # Pie chart for market share
        fig_pie = px.pie(
            values=list(continent_visitors.values()),
            names=list(continent_visitors.keys()),
            title="Continental Market Share",
            hole=0.4,
        )
        fig_pie.update_layout(
            height=450,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Emergence metrics
    st.write("**📊 Emergence Metrics:**")
    
    # Calculate Herfindahl-Hirschman Index (concentration)
    total_visitors = sum(continent_visitors.values())
    if total_visitors > 0:
        hhi = sum((v / total_visitors) ** 2 for v in continent_visitors.values())
        concentration = "Fragmented" if hhi < 0.2 else "Moderate" if hhi < 0.4 else "Concentrated"
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Regional Concentration (HHI)", f"{hhi:.3f}",
                      help="Higher = more concentrated tourism")
        with col2:
            st.metric("Pattern Type", concentration)
        with col3:
            st.metric("Continents with Tourism", len(continent_visitors))
    
    # Show top tourism corridors (origin-destination pairs)
    st.divider()
    st.write("**🛣️ Emergent Tourism Corridors:**")
    
    # Sample from trip records
    if sim.data_collector.trip_records:
        corridor_counts = defaultdict(int)
        for trip in sim.data_collector.trip_records[-1000:]:  # Last 1000 trips
            corridor = f"{trip['origin']} → {trip['destination']}"
            corridor_counts[corridor] += 1
        
        if corridor_counts:
            top_corridors = sorted(corridor_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Display in two columns
            col_corr1, col_corr2 = st.columns(2)
            
            for i, (corridor, count) in enumerate(top_corridors):
                origin_code = corridor.split(' → ')[0]
                dest_code = corridor.split(' → ')[1]
                origin_name = sim.destinations.get(origin_code)
                dest_name = sim.destinations.get(dest_code)
                
                corridor_text = f"  • **{origin_name.country_name if origin_name else origin_code} → {dest_name.country_name if dest_name else dest_code}**: {count} trips"
                
                if i < 5:
                    col_corr1.write(corridor_text)
                else:
                    col_corr2.write(corridor_text)
        else:
            st.info("No trip records yet - run simulation longer")
    else:
        st.info("Trip records not available - run simulation longer")
    
    st.caption("""
    **Emergence**: Global tourism patterns arise from individual agent decisions without
    central coordination. Tourism corridors, regional clusters, and seasonal waves are
    emergent phenomena that cannot be predicted from individual behavior alone.
    
    **Self-Organization**: Notice how certain corridors become dominant (e.g., USA→Europe, China→Asia)
    even though each agent makes independent decisions based on personal preferences.
    """)


import numpy as np


if __name__ == "__main__":
    main()
