#!/bin/bash
echo "Starting the HERE Mexico Hackathon app..."
echo "This will run the Flask server which serves the React app"
echo "Open your browser at http://localhost:5000"
source .venv/bin/activate
FLASK_APP=api.py FLASK_DEBUG=1 python3 api.py
