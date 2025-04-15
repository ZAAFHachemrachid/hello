#!/bin/bash
# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip to the latest version
pip install --upgrade pip

# Install build dependencies using pacman
sudo pacman -Syu --needed --noconfirm base-devel cmake pkg-config
sudo pacman -S --needed --noconfirm libx11 atlas gtk3 opencv opencv-samples python-opencv

# Install required dependencies from requirements.txt
pip install -r requirements.txt

echo "Virtual environment setup complete. Activate it with: source venv/bin/activate"