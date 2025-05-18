#!/bin/bash
# Script to start the application without building the frontend

echo "Starting the HERE Mexico Hackathon app in development mode..."
echo "This will run the Flask server at http://localhost:5000 and Vite dev server at http://localhost:5173"

# Start Vite dev server in background
cd Page
echo "Starting Vite development server..."
# Fix ports that are already in use
pkill -f "vite" || true
sleep 1
npx vite --host --port 5174 &
VITE_PID=$!

# Wait a moment for Vite to start
sleep 2

# Start Flask server
cd ..
echo "Starting Flask server..."
export FLASK_DEBUG=1
source .venv/bin/activate
python3 api.py

# When Flask exits, also kill Vite
kill $VITE_PID
