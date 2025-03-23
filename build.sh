#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt

# Tell Playwright to install in local folder (no root required)
export PLAYWRIGHT_BROWSERS_PATH=0
playwright install chromium
