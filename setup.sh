#!/bin/bash
# Streamlit Cloud Setup Script
# This runs before the app starts on Streamlit Cloud

mkdir -p ~/.streamlit/

echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml

echo "✅ Setup complete"
