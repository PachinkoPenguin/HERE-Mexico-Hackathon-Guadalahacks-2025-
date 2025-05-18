#!/bin/bash
# Script to install dependencies and build the project

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt || pip3 install -r requirements.txt

echo "Installing Node.js dependencies for the React app..."
cd Page
npm install --legacy-peer-deps
npm run build
cd ..

echo "Setup complete!"
echo "To run the application, use: ./run.sh"

cat > run.sh << 'EOF'
#!/bin/bash
echo "Starting the HERE Mexico Hackathon app..."
echo "This will run the Flask server which serves the React app"
echo "Open your browser at http://localhost:5000"
python3 api.py
EOF

chmod +x run.sh
