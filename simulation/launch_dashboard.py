#!/usr/bin/env python3
"""
Launch script for the Global Tourism Simulation Dashboard.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Streamlit dashboard."""
    dashboard_path = Path(__file__).parent / "visualization" / "dashboard.py"

    if not dashboard_path.exists():
        print(f"Error: Dashboard not found at {dashboard_path}")
        sys.exit(1)

    print("🌍 Launching Global Tourism Simulation Dashboard...")
    print(f"📍 Dashboard location: {dashboard_path}")
    print("")
    print("Dashboard will open in your default browser.")
    print("Press Ctrl+C to stop the dashboard.")
    print("")

    # Launch Streamlit
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(dashboard_path),
            "--server.headless",
            "true",
            "--server.address",
            "localhost",
            "--server.port",
            "8501",
        ]
    )


if __name__ == "__main__":
    main()
