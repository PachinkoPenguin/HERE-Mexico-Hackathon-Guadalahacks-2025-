# HERE Mexico Hackathon - Guadalahacks 2025

This project is a tool for verifying and visualizing Points of Interest (POIs) using HERE's mapping data. It solves the challenge of accurately positioning POIs on street segments based on their descriptive attributes.

## Features

- **POI Verification Tool**: Calculate the exact geographic coordinates of Points of Interest based on their position along street segments using PERCFRREF values.
- **Map Visualization**: Interactive maps showing streets, POIs, and their calculated positions for quick visual verification.
- **Tile Coordinate Calculator**: Convert geographic coordinates to map tile coordinates for use with HERE map tiles and other tile-based services.

## Project Structure

- `api.py`: Flask backend that serves the React app and provides API endpoints for running Python scripts
- `compararPOI.py`: Core functionality for POI verification and coordinate calculation
- `finalcode.py`: Utilities for working with map tiles and coordinates
- `POIs/`: Directory containing CSV files with POI data
- `STREETS_NAV/`: Directory containing GeoJSON files with street geometry data
- `STREETS_NAMING_ADDRESSING/`: Directory containing GeoJSON files with street naming data
- `Page/`: React frontend application
- `docs/`: Documentation and resources

## Installation and Setup

1. Clone this repository
2. Run the setup script:
   ```
   ./setup.sh
   ```
3. This will:
   - Install Python dependencies
   - Install Node.js dependencies
   - Build the React app

## Running the Application

To start the application, run:
```
./run.sh
```

This will start the Flask server which serves both the API endpoints and the React frontend.
Open your browser at http://localhost:5000 to access the application.

## Tools Available

1. **POI Verification Tool**:
   - Select a POI file and a street file
   - Choose a POI to verify
   - Click "Verify POI" to calculate its exact position
   - View the results on the map and in JSON format

2. **Tile Coordinate Calculator**:
   - Enter latitude and longitude
   - Select a zoom level
   - Calculate the corresponding map tile coordinates
   - View the location on the map

## Technology Stack

- **Frontend**: React, Vite, Leaflet, Tailwind CSS
- **Backend**: Python, Flask
- **Data Formats**: GeoJSON, CSV
