#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright and Chromium in Python environment
export PLAYWRIGHT_BROWSERS_PATH=0
npx playwright install chromium
