#!/bin/bash

# Upgrade pip and install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Tell Playwright to install Chromium locally (not as root)
export PLAYWRIGHT_BROWSERS_PATH=0
npx playwright install chromium
