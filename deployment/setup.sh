#!/bin/bash

# Exit on error
set -e

echo "Starting setup for Texas Hold'em Poker Game..."

# Update system packages
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Python and Git
echo "Installing Python3, pip, venv, and git..."
apt-get install -y python3 python3-pip python3-venv git

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete! You can now run the server using:"
echo "./venv/bin/uvicorn src.web.app:app --host 0.0.0.0 --port 8000"
