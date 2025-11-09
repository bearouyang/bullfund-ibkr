#!/bin/bash

# IBKR API Service Startup Script

echo "Starting IBKR API Service..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your IB Gateway/TWS settings"
fi

# Run the service
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
