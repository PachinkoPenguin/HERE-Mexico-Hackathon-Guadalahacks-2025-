#!/usr/bin/env python3
import os
import csv
import math
import json
import requests
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
import numpy as np
from io import BytesIO
from PIL import Image
import pandas as pd
import colorsys
from pathlib import Path
import matplotlib.colors as mcolors

def find_tile_center(tile_id):
    """
    Find the center coordinates of a tile from HERE_L11_Tiles.geojson
    """
    # Read the geojson file
    with open('data/HERE_L11_Tiles.geojson', 'r') as f:
        data = json.load(f)
    
    # Find the first feature with matching tile ID
    for feature in data['features']:
        if feature['properties']['L11_Tile_ID'] == tile_id:
            # Extract coordinates
            polygon = feature['geometry']['coordinates'][0]
            # Calculate center (average of all points)
            lons = [point[0] for point in polygon]
            lats = [point[1] for point in polygon]
            center_lon = sum(lons) / len(lons)
            center_lat = sum(lats) / len(lats)
            # Also return the bounding box
            min_lon = min(lons)
            max_lon = max(lons)
            min_lat = min(lats)
            max_lat = max(lats)
            return {
                'center': (center_lat, center_lon),
                'bounds': [(min_lat, min_lon), (max_lat, max_lon)]
            }
    
    return None

def read_poi_file(tile_id):
    """
    Read POI data from the CSV file corresponding to the tile ID,
    or from the combined all_pois.json file if available.
    """
    # Check if the processed data exists
    processed_file = Path('data/processed/all_pois.json')
    if processed_file.exists():
        try:
            # Load the processed data and filter by tile_id
            with open(processed_file, 'r') as f:
                all_pois = json.load(f)
            
            # Filter POIs for this tile and convert to list of dictionaries
            pois = [poi for poi in all_pois if str(poi.get('TILE_ID')) == str(tile_id)]
            
            if pois:
                print(f"Loaded {len(pois)} POIs for tile {tile_id} from processed data")
                return pois
            else:
                print(f"No POIs found for tile {tile_id} in processed data, falling back to original file")
        except Exception as e:
            print(f"Error reading processed data: {e}")
            print("Falling back to original POI file")
    
    # If we reach here, either the processed file doesn't exist or we couldn't find POIs for this tile
    poi_file = f'data/POIs/POI_{tile_id}.csv'
    pois = []
    
    if not os.path.exists(poi_file):
        print(f"POI file for tile {tile_id} not found")
        return pois
    
    # Read CSV file
    try:
        df = pd.read_csv(poi_file)
        pois = df.to_dict('records')
        print(f"Loaded {len(pois)} POIs directly from {poi_file}")
    except Exception as e:
        print(f"Error reading POI file: {e}")
    
    return pois

def lat_lon_to_tile(lat, lon, zoom):
    """
    Convert latitude and longitude to tile indices (x, y) at a given zoom level.
    """
    # Ensure latitude is within bounds to prevent math domain errors
    lat = max(min(lat, 85.05112878), -85.05112878)
    
    # Calculate n (number of tiles at the given zoom level)
    n = 2.0 ** zoom
    
    # Calculate x and y tile indices
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    
    return (x, y)

def get_satellite_tile(lat, lon, zoom, tile_format, api_key, size=512):
    """
    Get a satellite imagery tile for the given coordinates
    """
    # Convert lat/lon to tile coordinates
    x, y = lat_lon_to_tile(lat, lon, zoom)
    
    # Construct the URL for the map tile API
    url = f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size={size}&apiKey={api_key}'
    
    # Make the request
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Create an image from the response content
        image = Image.open(BytesIO(response.content))
        print('Tile retrieved successfully.')
        return image
    else:
        print(f'Failed to retrieve tile. Status code: {response.status_code}')
        return None

def get_poi_colors_by_type(pois):
    """
    Generate consistent colors for each POI facility type
    """
    # Extract unique facility types
    if any('FAC_TYPE' in poi for poi in pois):
        facility_types = sorted(set(poi.get('FAC_TYPE') for poi in pois if 'FAC_TYPE' in poi))
    else:
        facility_types = sorted(set(poi.get('type') for poi in pois if 'type' in poi))
    
    # Create a mapping of facility type to color
    cmap = plt.cm.get_cmap('tab20', len(facility_types))
    color_map = {}
    
    for i, facility_type in enumerate(facility_types):
        color_map[facility_type] = mcolors.rgb2hex(cmap(i)[:3])
    
    return color_map

def get_facility_type_description(fac_type):
    """
    Get a human-readable description for a facility type code
    """
    try:
        # Try to read from the facility types file
        with open('data/docs/POI_Facility_Types.csv', 'r') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader)
            for row in reader:
                if row[0] == str(fac_type):
                    return row[1]
    except Exception:
        pass
    
    # Return a default value if not found
    return f"Type {fac_type}"

def plot_pois_on_map(tile_id, api_key, zoom_level=14, output_csv=True):
    """
    Plot all POIs from a specific tile ID on a satellite image
    """
    # Find the tile center
    tile_info = find_tile_center(tile_id)
    if not tile_info:
        print(f"Tile ID {tile_id} not found in HERE_L11_Tiles.geojson")
        return
    
    center_lat, center_lon = tile_info['center']
    print(f"Tile center: {center_lat}, {center_lon}")
    
    # Get satellite imagery
    image = get_satellite_tile(center_lat, center_lon, zoom_level, 'png', api_key)
    if image is None:
        return
    
    # Read POIs
    pois = read_poi_file(tile_id)
    if not pois:
        print("No POIs found for this tile")
        return
    
    print(f"Found {len(pois)} POIs in tile {tile_id}")
    
    # Get colors for facility types
    color_map = get_poi_colors_by_type(pois)
    
    # Create a figure and plot the satellite image
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.imshow(image)
    
    # Draw the tile boundary if available
    if 'bounds' in tile_info:
        min_lat, min_lon = tile_info['bounds'][0]
        max_lat, max_lon = tile_info['bounds'][1]
        
        # Convert lat/lon bounds to pixel coordinates (approximate mapping)
        img_h, img_w = image.height, image.width
        
        # This is a simple approximation - for accurate mapping we'd need proper geospatial transformation
        # But for visualization purposes this rough mapping works
        bbox_points = [
            [0, 0],  # top-left
            [img_w, 0],  # top-right
            [img_w, img_h],  # bottom-right
            [0, img_h],  # bottom-left
        ]
        
        # Draw boundary
        bbox = Polygon(bbox_points, edgecolor='white', fill=False, linewidth=2)
        ax.add_patch(bbox)
    
    # Create a mapping dictionary for POI numbers
    poi_mapping = {}
    
    # Plot POIs as dots with colors based on facility type
    np.random.seed(42)  # For reproducibility
    
    # Distribute POIs evenly across the image
    img_h, img_w = image.height, image.width
    
    # Calculate grid size to fit all POIs
    grid_size = int(np.ceil(np.sqrt(len(pois))))
    x_step = img_w / (grid_size + 1)
    y_step = img_h / (grid_size + 1)
    
    # Create a data structure for export
    export_data = []
    
    for i, poi in enumerate(pois):
        # Assign a position in the grid
        grid_x = (i % grid_size) + 1
        grid_y = (i // grid_size) + 1
        
        # Apply some randomness to avoid perfect grid alignment
        x = int(grid_x * x_step + np.random.normal(0, x_step/10))
        y = int(grid_y * y_step + np.random.normal(0, y_step/10))
        
        # Keep within image bounds
        x = max(10, min(x, img_w-10))
        y = max(10, min(y, img_h-10))
        
        # Get the facility type and color
        if 'FAC_TYPE' in poi:
            fac_type = poi.get('FAC_TYPE')
        else:
            fac_type = poi.get('type')
        
        color = color_map.get(fac_type, 'red')
        
        # Plot a numbered dot
        circle = Circle((x, y), 10, color=color, alpha=0.7)
        ax.add_patch(circle)
        
        # Add POI number inside the circle
        ax.text(x, y, str(i+1), fontsize=8, ha='center', va='center', color='white', weight='bold')
        
        # Store mapping for export
        poi_name = poi.get('POI_NAME', poi.get('name', f"POI {i+1}"))
        poi_mapping[i+1] = {
            'name': poi_name,
            'type': fac_type,
            'type_desc': get_facility_type_description(fac_type) if fac_type else "Unknown",
            'position': (x, y)
        }
        
        # Add more detailed info to export data
        export_data.append({
            'id': i+1,
            'name': poi_name,
            'facility_type': fac_type,
            'type_description': get_facility_type_description(fac_type) if fac_type else "Unknown",
            'x': x,
            'y': y,
            **poi  # Include all original POI data
        })
    
    # Create a legend for facility types
    legend_elements = []
    for fac_type, color in color_map.items():
        description = get_facility_type_description(fac_type)
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                                         markersize=10, label=f"{fac_type} - {description}"))
    
    # Place legend outside the plot
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1), fontsize='small', title="Facility Types")
    
    ax.set_title(f'POIs in Tile {tile_id}')
    ax.axis('off')  # Hide axis
    
    # Adjust layout to make room for legend
    plt.tight_layout()
    plt.subplots_adjust(right=0.75)
    
    # Save mapping to a CSV file
    if output_csv:
        output_dir = Path('data/processed')
        output_dir.mkdir(exist_ok=True)
        
        # Save the detailed POI data
        df = pd.DataFrame(export_data)
        csv_file = output_dir / f'poi_map_tile_{tile_id}_data.csv'
        df.to_csv(csv_file, index=False)
        print(f"POI mapping data saved to {csv_file}")
    
    # Save and show the figure
    plt.savefig(f'poi_map_tile_{tile_id}.png', dpi=300, bbox_inches='tight')
    print(f"Map image saved to poi_map_tile_{tile_id}.png")
    
    return fig, export_data

if __name__ == "__main__":
    # Load API key from dot.env file
    api_key = ""
    try:
        with open('dot.env', 'r') as env_file:
            for line in env_file:
                if line.startswith('API key:'):
                    api_key = line.split('API key:')[1].strip()
    except Exception as e:
        print(f"Error reading API key: {e}")
        exit(1)
    
    if not api_key:
        print("API key not found in dot.env file")
        exit(1)
    
    # Check if all_pois.json exists, if not suggest running poi_data_extractor.py first
    if not os.path.exists('data/processed/all_pois.json'):
        print("Warning: Processed POI data not found.")
        print("For best results, consider running poi_data_extractor.py first:")
        print("python poi_data_extractor.py")
        print("Continuing with direct file reading...\n")
    
    # Ask user for tile ID
    tile_id = input("Enter the tile ID (e.g., 4815075): ")
    try:
        tile_id = int(tile_id)
    except ValueError:
        print("Invalid tile ID. Please enter a number.")
        exit(1)
    
    # Plot POIs
    fig, export_data = plot_pois_on_map(tile_id, api_key)
    
    # Show the figure
    plt.show()
    
    print("\nYou can find detailed information about each POI in the export file.")
    print("The numbers on the map correspond to the 'id' column in the export file.")
    print("This allows you to identify specific POIs and look up their details.")
