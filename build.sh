#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- Installing dependencies ---"
pip install -r requirements.txt

export FLASK_APP=app.py

echo "--- Running database migrations ---"
flask db upgrade

echo "--- Seeding project data ---"
flask seed-projects

echo "--- Build finished ---"