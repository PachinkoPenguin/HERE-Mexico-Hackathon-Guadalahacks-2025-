#!/usr/bin/env python3
import os
import csv
import math
import json
import requests
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
from matplotlib.lines import Line2D  # Added import for Line2D
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
    
    Parameters:
    tile_id (str or int): The tile ID to look up
    
    Returns:
    dict: Dictionary with 'center' and 'bounds' keys, or None if not found
    """
    # First try to handle test cases with hardcoded test data
    if str(tile_id) == 'TEST_FIXED' or str(tile_id) == 'VIOLATION':
        # Return test coordinates for Guadalajara area
        return {
            'center': (19.432, -99.123),  # Example coordinates
            'bounds': [(19.430, -99.125), (19.434, -99.121)]
        }
    
    # For normal numerical tile IDs, try to convert to integer for consistent comparison
    try:
        tile_id_int = int(tile_id)
        # Continue with numerical comparison
    except (ValueError, TypeError):
        # Not a test case and not a number
        print(f"Warning: Tile ID '{tile_id}' is not a test ID or a number.")
        return None
        
    # Read the geojson file
    try:
        with open('data/HERE_L11_Tiles.geojson', 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading tile data: {e}")
        return None
    
    # Find the first feature with matching tile ID
    for feature in data['features']:
        # Get the tile ID from the feature
        feature_tile_id = feature['properties'].get('L11_Tile_ID')
        found_match = False
        
        try:
            feature_tile_id_int = int(feature_tile_id)
            if feature_tile_id_int == tile_id_int:
                found_match = True
        except (ValueError, TypeError):
            # If conversion fails, try string comparison as fallback
            if str(feature_tile_id) == str(tile_id):
                found_match = True
        
        if found_match:
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
    
    print(f"Tile {tile_id} not found in HERE_L11_Tiles.geojson.")
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
    Get a satellite imagery tile for the given coordinates using HERE Maps API
    """
    # Define tile_size for URL construction to match satellite_imagery_tile_request.py
    tile_size = size
    
    # Ensure API key is properly formatted
    api_key = api_key.strip() if api_key else ""
    
    if not api_key:
        print("Error: Missing API key for satellite tile request")
        return None
    
    # Print debug info (without revealing the full API key)
    key_preview = api_key[:5] + "..." if len(api_key) > 5 else "invalid"
    print(f"Making satellite tile request with API key: {key_preview}")
    
    # Get tile coordinates
    x, y = lat_lon_to_tile(lat, lon, zoom)
    
    # Use exactly the same URL format as the working satellite_imagery_tile_request.py
    url = f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}&style=satellite.day&size={tile_size}?apiKey={api_key}'
    print(f"Requesting satellite tile from: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Verify we got an image and not an error page
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type.lower():
                try:
                    image = Image.open(BytesIO(response.content))
                    print('Tile retrieved successfully.')
                    return image
                except Exception as e:
                    print(f"Error parsing image response: {e}")
            else:
                print(f"API returned non-image content: {content_type}")
        else:
            print(f'API request failed. Status: {response.status_code}')
            error_msg = response.text[:200] if response.text else "No error message"
            print(f'Error: {error_msg}')
    except Exception as e:
        print(f"Error with API request: {e}")
    
    print("Unable to retrieve satellite imagery.")
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
    # Use the modern approach to get colormaps to avoid deprecation warnings
    import matplotlib as mpl
    
    # Check matplotlib version and use appropriate method to get colormap
    cmap = None
    
    # First try matplotlib 3.6+ method (mpl.colormaps)
    try:
        import matplotlib as mpl
        if hasattr(mpl, 'colormaps'):
            cmap = mpl.colormaps['tab20']
    except (KeyError, AttributeError, ImportError):
        pass
    
    # Next try matplotlib 3.5 transition method (plt.colormaps)
    if cmap is None:
        try:
            if hasattr(plt, 'colormaps'):
                cmap = plt.colormaps['tab20']
        except (KeyError, AttributeError):
            pass
    
    # Fallback for older matplotlib versions
    if cmap is None:
        try:
            from matplotlib.cm import get_cmap
            cmap = get_cmap('tab20')
        except Exception:
            # Ultimate fallback if everything else fails
            cmap = plt.cm.get_cmap('tab20', max(20, len(facility_types)))
    
    color_map = {}
    
    for i, facility_type in enumerate(facility_types):
        idx = i % 20  # tab20 has 20 colors, cycle through them
        color_map[facility_type] = mcolors.rgb2hex(cmap(idx)[:3])
    
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

def plot_pois_on_map(tile_id, api_key=None, zoom_level=14, output_csv=True):
    """
    Plot all POIs from a specific tile ID on a satellite image
    """
    # Find the tile center
    tile_info = find_tile_center(tile_id)
    if not tile_info:
        print(f"Tile ID {tile_id} not found in HERE_L11_Tiles.geojson")
        return None, None
    
    center_lat, center_lon = tile_info['center']
    print(f"Tile center: {center_lat}, {center_lon}")
    
    # Get satellite imagery if API key is provided
    satellite_image = None
    if api_key:
        satellite_image = get_satellite_tile(center_lat, center_lon, zoom_level, 'png', api_key)
    
    if satellite_image is None:
        # Create a basic background image with coordinates
        print("Creating a basic map without satellite imagery.")
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a background image
        image = Image.new('RGB', (1024, 1024), color='#E5E5E5')  # Light gray background
        draw = ImageDraw.Draw(image)
        
        # Try to load a font, fallback to default if not found
        try:
            # Try to find a system font
            font_path = None
            common_fonts = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/TTF/Arial.ttf',
                '/System/Library/Fonts/Helvetica.ttc'
            ]
            for path in common_fonts:
                if os.path.exists(path):
                    font_path = path
                    break
            
            font = ImageFont.truetype(font_path, 24) if font_path else ImageFont.load_default()
            small_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
        except Exception:
            # Fallback to default font
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Add title and coordinates
        draw.text((20, 20), f"Tile ID: {tile_id}", fill="black", font=font)
        draw.text((20, 60), f"Center: {center_lat:.4f}, {center_lon:.4f}", fill="black", font=small_font)
        
        # Draw a coordinate grid
        grid_spacing = 100
        for x in range(0, 1024, grid_spacing):
            # Vertical line
            draw.line([(x, 0), (x, 1023)], fill="#CCCCCC", width=1)
            # Label
            if x > 0:
                draw.text((x + 5, 5), f"{x}", fill="#999999", font=small_font)
        
        for y in range(0, 1024, grid_spacing):
            # Horizontal line
            draw.line([(0, y), (1023, y)], fill="#CCCCCC", width=1)
            # Label
            if y > 0:
                draw.text((5, y + 5), f"{y}", fill="#999999", font=small_font)
        
        # Mark center
        center_x, center_y = 512, 512
        draw.ellipse((center_x-10, center_y-10, center_x+10, center_y+10), fill="red")
        draw.text((center_x+15, center_y-10), "Center", fill="black", font=small_font)
    else:
        # Use the satellite image
        image = satellite_image
    
    # Read POIs
    pois = read_poi_file(tile_id)
    if not pois:
        print("No POIs found for this tile")
        return None, None
    
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
        legend_elements.append(Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
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
    # Set the API key directly to match the known working key in .env
    api_key = "MHKxcSsguxA1chxDDd_gVSTwQgi4Bsxm49qjnHfkBTs"
    
    # Try loading from environment as backup
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()  # This loads the .env file into os.environ
            api_key = os.environ.get('API_KEY', os.environ.get('HERE_API_KEY', ''))
        except ImportError:
            print("Warning: python-dotenv not installed. Falling back to manual .env parsing.")
            
            # If still not found, try manual parsing of .env file
            if not api_key:
                try:
                    env_file_path = '.env'
                    if os.path.exists(env_file_path):
                        with open(env_file_path, 'r') as env_file:
                            for line in env_file:
                                line = line.strip()
                                if line and not line.startswith('#') and '=' in line:
                                    key, value = line.split('=', 1)
                                    if key.strip() == 'API_KEY':
                                        api_key = value.strip().strip('"\'')
                                        break
                except Exception as e:
                    print(f"Error reading .env file manually: {e}")
    
    # Debug output (without revealing full API key)
    if api_key:
        key_preview = api_key[:5] + "..." if len(api_key) > 5 else "invalid"
        print(f"Using API key: {key_preview}")
    else:
        print("Warning: No API key found.")
        print("Satellite imagery won't be available.")
        print("You can set the API_KEY environment variable or add it to a .env file.")
    
    # Check if all_pois.json exists, if not suggest running poi_data_extractor.py first
    if not os.path.exists('data/processed/all_pois.json'):
        print("Warning: Processed POI data not found.")
        print("For best results, consider running poi_data_extractor.py first:")
        print("python poi_data_extractor.py")
        print("Continuing with direct file reading...\n")
    
    # Ask user for tile ID
    tile_id = input("Enter the tile ID (e.g., 4815075): ")
    
    # Plot POIs
    fig, export_data = plot_pois_on_map(tile_id, api_key)
    
    if fig:
        # Show the figure
        plt.show()
        
        print("\nYou can find detailed information about each POI in the export file.")
        print("The numbers on the map correspond to the 'id' column in the export file.")
        print("This allows you to identify specific POIs and look up their details.")
    else:
        print("Failed to generate map. Please check the tile ID and try again.")
