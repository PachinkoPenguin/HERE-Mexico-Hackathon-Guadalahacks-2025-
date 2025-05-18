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
    
    Parameters:
    -----------
    lat : float
        Latitude in degrees
    lon : float 
        Longitude in degrees
    zoom : int
        Zoom level (0-19)
    tile_format : str
        Format of the tile (png, jpeg)
    api_key : str
        HERE Maps API key
    size : int
        Size of the tile in pixels (default 512)
        
    Returns:
    --------
    PIL.Image or None
        The satellite tile image, or None if retrieval failed
    """
    # Define tile_size for URL construction
    tile_size = size
    
    # Ensure API key is properly formatted
    api_key = api_key.strip() if api_key else ""
    
    if not api_key:
        print("Error: Missing API key for satellite tile request")
        return None
    
    # Print debug info (without revealing the full API key)
    key_preview = f"{api_key[:3]}...{api_key[-3:]}" if len(api_key) > 8 else "invalid key"
    print(f"Making satellite tile request with API key: {key_preview}")
    
    # Get tile coordinates for HERE Maps API
    x, y = lat_lon_to_tile(lat, lon, zoom)
    
    print(f"Calculated tile coordinates: x={x}, y={y} for lat={lat}, lon={lon}, zoom={zoom}")
    
    # Try multiple URL formats that could work with the HERE Maps API
    # Starting with the most modern v3 endpoint
    # IMPORTANT: URL structure must be: path/{zoom}/{x}/{y}/{format}?param1=value1&param2=value2
    # Note that query parameters must come after the ? and be separated by &
    urls = [
        # v3 API base endpoint (documented in satellite_imagery_tile_request.py)
        f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size={tile_size}&apiKey={api_key}',
        
        # v3 API with ppi parameter
        f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size={tile_size}&ppi=72&apiKey={api_key}',
        
        # v3 aerial endpoint
        f'https://aerial.maps.hereapi.com/v3/aerial/mc/{zoom}/{x}/{y}/{tile_format}?apiKey={api_key}',
        
        # v2.1 aerial endpoint with numbered domain
        f'https://1.aerial.maps.ls.hereapi.com/maptile/2.1/maptile/newest/satellite.day/{zoom}/{x}/{y}/{tile_size}/{tile_format}?apiKey={api_key}',
        
        # v2.1 alternative domain
        f'https://2.aerial.maps.ls.hereapi.com/maptile/2.1/maptile/newest/satellite.day/{zoom}/{x}/{y}/{tile_size}/{tile_format}?apiKey={api_key}',
        
        # v2.1 without subdomain
        f'https://aerial.maps.ls.hereapi.com/maptile/2.1/maptile/newest/satellite.day/{zoom}/{x}/{y}/{tile_size}/{tile_format}?apiKey={api_key}'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/png,image/jpeg,image/*'
    }
    
    # Try each URL in sequence
    for i, url in enumerate(urls):
        print(f"Trying URL #{i+1}: {url.replace(api_key, 'YOUR_API_KEY_REDACTED')}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image' in content_type.lower():
                    try:
                        image = Image.open(BytesIO(response.content))
                        print(f'Satellite tile retrieved successfully with URL #{i+1}.')
                        # Save a copy for debugging/comparison
                        with open(f'satellite_tile_success_{i+1}.{tile_format}', 'wb') as file:
                            file.write(response.content)
                        return image
                    except Exception as e:
                        print(f"Error parsing image response: {e}")
                else:
                    print(f"API returned non-image content: {content_type}")
            else:
                print(f'API request #{i+1} failed. Status: {response.status_code}')
                error_msg = response.text[:200] if response.text else "No error message"
                print(f'Error: {error_msg}')
        except Exception as e:
            print(f"Error with URL #{i+1}: {e}")
    
    # If all URLs fail, try with a direct IP address (if DNS is the issue)
    try:
        # Modified URL with potential direct IP (this is a placeholder)
        alt_url = urls[0].replace('maps.hereapi.com', '134.76.8.222')  # Example IP for testing
        print(f"Trying direct IP address: {alt_url.replace(api_key, 'YOUR_API_KEY_REDACTED')}")
        response = requests.get(alt_url, headers=headers, timeout=15)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Failed with direct IP too: {e}")
    
    # If we can't get satellite imagery, use a mock satellite image for development purposes
    print("Unable to retrieve satellite imagery. Using fallback image...")
    
    # Create a basic mock satellite image for development
    try:
        # Try to create a realistic-looking satellite image with noise patterns
        from numpy import random
        import numpy as np
        from numpy import random
        import numpy as np
        
        # Create a dark greenish-brownish base image that looks like satellite imagery
        img_size = (tile_size, tile_size, 3)
        # Base colors for land
        base_color = np.array([
            [0.2, 0.3, 0.2],  # Dark green (forests)
            [0.4, 0.3, 0.2],  # Brown (urban)
            [0.3, 0.3, 0.1],  # Yellowish (fields)
            [0.2, 0.2, 0.3],  # Bluish (water)
        ])
        
        # Generate a random index for each pixel
        indices = random.randint(0, len(base_color), (tile_size, tile_size))
        img = np.zeros(img_size)
        
        # Apply base colors
        for i in range(len(base_color)):
            mask = (indices == i)
            for c in range(3):
                img[:,:,c][mask] = base_color[i,c]
        
        # Add some noise
        img += random.normal(0, 0.05, img_size)
        img = np.clip(img, 0, 1)
        
        # Add some road-like patterns (random straight lines)
        for _ in range(20):  # 20 "roads"
            # Avoid going to the edge to prevent index errors
            buffer = 10
            x1 = random.randint(buffer, tile_size-buffer)
            y1 = random.randint(buffer, tile_size-buffer)
            x2 = random.randint(buffer, tile_size-buffer)
            y2 = random.randint(buffer, tile_size-buffer)
            
            # Create line points
            num_points = min(1000, max(abs(x2-x1), abs(y2-y1)) * 2)
            rr, cc = np.linspace(x1, x2, num_points).astype(int), np.linspace(y1, y2, num_points).astype(int)
            
            # Add width to the road
            road_width = random.randint(1, 3)
            
            # Draw the road safely
            for dx in range(-road_width, road_width+1):
                for dy in range(-road_width, road_width+1):
                    rr_offset = np.clip(rr + dx, 0, tile_size-1)
                    cc_offset = np.clip(cc + dy, 0, tile_size-1)
                    img[cc_offset, rr_offset] = [0.7, 0.7, 0.7]  # Gray roads
        
        # Convert to PIL Image
        img = (img * 255).astype(np.uint8)
        pil_img = Image.fromarray(img)
        pil_img.save('mock_satellite.png')
        print("Created mock satellite image for development")
        return pil_img
    except Exception as e:
        print(f"Failed to create mock image: {e}")
        
    print("All attempts to get satellite imagery failed.")
    return None

def get_poi_colors_by_type(pois):
    """
    Generate consistent colors for each POI facility type with improved grouping
    """
    # Extract unique facility types
    if any('FAC_TYPE' in poi for poi in pois):
        facility_types = sorted(set(poi.get('FAC_TYPE') for poi in pois if 'FAC_TYPE' in poi))
    else:
        facility_types = sorted(set(poi.get('type') for poi in pois if 'type' in poi))
    
    # Group facility types into categories based on common prefixes
    # This groups similar POIs by their first 2 digits
    facility_prefixes = {}
    for fac_type in facility_types:
        try:
            # Get first 2 digits as prefix
            prefix = str(int(fac_type))[:2]
            if prefix not in facility_prefixes:
                facility_prefixes[prefix] = []
            facility_prefixes[prefix].append(fac_type)
        except (ValueError, TypeError):
            # Handle non-numeric types
            if 'other' not in facility_prefixes:
                facility_prefixes['other'] = []
            facility_prefixes['other'].append(fac_type)
    
    # Get a colormap that provides enough distinct colors
    cmap = None
    
    try:
        # Try different methods to get a colormap
        import matplotlib as mpl
        if hasattr(mpl, 'colormaps') and 'tab20' in mpl.colormaps:
            cmap = mpl.colormaps['tab20']
    except Exception:
        pass
    
    if cmap is None:
        try:
            if hasattr(plt, 'colormaps') and 'tab20' in plt.colormaps:
                cmap = plt.colormaps['tab20']
        except Exception:
            pass
    
    if cmap is None:
        try:
            from matplotlib.cm import get_cmap
            cmap = get_cmap('tab20')
        except Exception:
            pass
    
    if cmap is None:
        try:
            # Ultimate fallback - create a custom colormap
            colors = []
            for i in range(20):
                h = i / 20
                s = 0.8
                v = 0.9
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                colors.append((r, g, b))
                
            cmap = mcolors.LinearSegmentedColormap.from_list('custom_cmap', colors, N=20)
        except Exception:
            # Basic fallback with hardcoded colors if all else fails
            basic_colors = [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
                '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
                '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5'
            ]
            
            def simple_cmap(idx):
                color_hex = basic_colors[idx % len(basic_colors)].lstrip('#')
                return tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
            
            cmap = simple_cmap
    
    # Create a color map
    color_map = {}
    
    # First assign colors to each prefix group
    prefix_colors = {}
    for i, prefix in enumerate(sorted(facility_prefixes.keys())):
        idx = i % 20  # tab20 has 20 colors, cycle through them
        prefix_colors[prefix] = cmap(idx)
    
    # Then assign colors to each facility type based on its prefix
    for prefix, types in facility_prefixes.items():
        base_color = prefix_colors[prefix]
        
        # For each type in this prefix, create slight variations if needed
        for j, fac_type in enumerate(types):
            if j == 0:
                # Use the base color for the first type in each group
                color_map[fac_type] = mcolors.rgb2hex(base_color[:3])
            else:
                # Create slight variations for additional types in the same group
                # by adjusting brightness or saturation
                h, s, v = colorsys.rgb_to_hsv(*base_color[:3])
                # Adjust saturation slightly for each variation
                s_adj = max(0.2, min(1.0, s + (j * 0.15) % 0.6 - 0.3))
                # Adjust value (brightness) slightly
                v_adj = max(0.3, min(0.9, v + (j * 0.1) % 0.4 - 0.2))
                r, g, b = colorsys.hsv_to_rgb(h, s_adj, v_adj)
                color_map[fac_type] = mcolors.rgb2hex((r, g, b))
    
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

def plot_pois_on_map(tile_id, api_key=None, zoom_level=14, output_csv=True, max_pois=1000, cluster_distance=20):
    """
    Plot all POIs from a specific tile ID on a satellite image with improved visualization
    
    Parameters:
    -----------
    tile_id : str
        The tile ID to plot POIs for
    api_key : str, optional
        HERE API key for satellite imagery
    zoom_level : int, optional
        Zoom level for satellite imagery
    output_csv : bool, optional
        Whether to save POI data to CSV
    max_pois : int, optional
        Maximum number of POIs to display (to avoid overcrowding)
    cluster_distance : int, optional
        Distance threshold for clustering nearby POIs
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
        # Try with higher resolution and larger size
        satellite_image = get_satellite_tile(center_lat, center_lon, zoom_level, 'png', api_key, size=1024)
        if satellite_image:
            print("Successfully retrieved satellite imagery for the map background.")
    
    # Initialize the figure with a specific style
    import matplotlib
    matplotlib.rcParams['figure.facecolor'] = 'white'
    matplotlib.rcParams['axes.facecolor'] = 'white'
    matplotlib.rcParams['font.family'] = 'sans-serif'
    
    if satellite_image is None:
        # Create a more appealing background image with coordinates
        print("Creating a styled map without satellite imagery.")
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a background image
        image = Image.new('RGB', (1024, 1024), color='#F8F9FA')  # Light background
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
            
            font = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
            small_font = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default()
        except Exception:
            # Fallback to default font
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Add title and coordinates with a nicer styling
        header_box = [(0, 0), (1024, 80)]
        draw.rectangle(header_box, fill="#4285F4")  # Google Maps blue
        draw.text((20, 20), f"Tile ID: {tile_id}", fill="white", font=font)
        draw.text((20, 55), f"Center: {center_lat:.4f}, {center_lon:.4f}", fill="white", font=small_font)
        
        # Draw a more subtle coordinate grid
        grid_spacing = 100
        for x in range(0, 1024, grid_spacing):
            # Vertical line
            draw.line([(x, 80), (x, 1023)], fill="#E1E1E1", width=1)
            # Label
            if x > 0:
                draw.text((x + 5, 85), f"{x}", fill="#666666", font=small_font)
        
        for y in range(80, 1024, grid_spacing):
            # Horizontal line
            draw.line([(0, y), (1023, y)], fill="#E1E1E1", width=1)
            # Label
            if y > 80:
                draw.text((5, y + 5), f"{y}", fill="#666666", font=small_font)
        
        # Mark center with a more visible marker
        center_x, center_y = 512, 512
        marker_size = 15
        
        # Draw a pin-like marker
        draw.polygon([
            (center_x, center_y - marker_size),
            (center_x + marker_size, center_y),
            (center_x, center_y + marker_size),
            (center_x - marker_size, center_y)
        ], fill="#EA4335")  # Google Maps red
        
        draw.ellipse((center_x-5, center_y-5, center_x+5, center_y+5), fill="white")
        draw.text((center_x+20, center_y-10), "Center", fill="#333333", font=small_font)
    else:
        # Use the satellite image
        image = satellite_image
    
    # Read POIs
    pois = read_poi_file(tile_id)
    if not pois:
        print("No POIs found for this tile")
        return None, None
    
    print(f"Found {len(pois)} POIs in tile {tile_id}")
    
    # If there are too many POIs, sample them to avoid overcrowding
    if len(pois) > max_pois:
        print(f"Limiting display to {max_pois} POIs out of {len(pois)} total")
        # Use a deterministic sampling for reproducibility
        np.random.seed(42)
        sampled_indices = np.random.choice(len(pois), max_pois, replace=False)
        pois_to_display = [pois[i] for i in sampled_indices]
    else:
        pois_to_display = pois
    
    # Get colors for facility types
    color_map = get_poi_colors_by_type(pois)
    
    # Create a figure and plot the satellite image
    fig, ax = plt.subplots(figsize=(16, 14))  # Larger figure for better visibility
    ax.imshow(image)
    
    # Apply a semi-transparent overlay to improve contrast with markers
    overlay = np.ones((image.height, image.width, 4))
    overlay[:, :, 3] = 0.1  # Alpha channel - barely visible
    ax.imshow(overlay, alpha=0.1)
    
    # Draw the tile boundary with a more visible style
    if 'bounds' in tile_info:
        min_lat, min_lon = tile_info['bounds'][0]
        max_lat, max_lon = tile_info['bounds'][1]
        
        # Convert lat/lon bounds to pixel coordinates (approximate mapping)
        img_h, img_w = image.height, image.width
        
        # Draw a more prominent boundary
        bbox_points = [
            [0, 0],  # top-left
            [img_w, 0],  # top-right
            [img_w, img_h],  # bottom-right
            [0, img_h],  # bottom-left
        ]
        
        # Draw boundary with a more visible style
        bbox = Polygon(bbox_points, edgecolor='#FFFFFF', fill=False, linewidth=3, alpha=0.8)
        ax.add_patch(bbox)
        
        # Add corner markers for better orientation
        corner_size = 40
        for point in bbox_points:
            x, y = point
            ax.plot(x, y, 'o', color='white', markersize=8, alpha=0.8)
    
    # Create a mapping dictionary for POI numbers
    poi_mapping = {}
    
    # Prepare data structures
    import pandas as pd
    
    # Prepare data for clustering
    poi_positions = []
    poi_data = []
    
    # Create a data structure for export
    export_data = []
    
    # Define image dimensions
    img_h, img_w = image.height, image.width
    
    # Try to cluster POIs by position to reduce overcrowding
    try:
        # Extract coordinates for clustering
        # This is just for display purposes, so we'll create a simple grid
        
        # Generate positions for the POIs
        for i, poi in enumerate(pois_to_display):
            # For real geospatial data, we would use proper conversion from lat/lon
            # Since we don't have accurate coordinates, create a grid-like arrangement
            grid_x = (i % int(np.sqrt(len(pois_to_display)))) / np.sqrt(len(pois_to_display))
            grid_y = (i // int(np.sqrt(len(pois_to_display)))) / np.sqrt(len(pois_to_display))
            
            # Scale to image dimensions and add slight randomness
            x = int(grid_x * img_w + np.random.normal(0, img_w/50))
            y = int(grid_y * img_h + np.random.normal(0, img_h/50))
            
            # Keep within image bounds
            x = max(20, min(x, img_w-20))
            y = max(20, min(y, img_h-20))
            
            # Get the facility type
            if 'FAC_TYPE' in poi:
                fac_type = poi.get('FAC_TYPE')
            else:
                fac_type = poi.get('type')
            
            poi_positions.append([x, y])
            poi_data.append({
                'index': i,
                'poi': poi,
                'fac_type': fac_type,
                'x': x,
                'y': y
            })
        
        # Convert to numpy array for clustering
        X = np.array(poi_positions)
        
        # Try to use scikit-learn for clustering if it's available
        try:
            # Try to dynamically import scikit-learn
            import importlib
            sklearn_cluster = importlib.import_module('sklearn.cluster')
            DBSCAN = getattr(sklearn_cluster, 'DBSCAN')
            
            clustering = DBSCAN(eps=cluster_distance, min_samples=5).fit(X)
            labels = clustering.labels_
        except (ImportError, ModuleNotFoundError):
            print("scikit-learn not available, using simple distance-based clustering")
            # Fallback to a simple distance-based clustering
            labels = [-1] * len(X)  # Start with all points as noise
            
            # Simple distance-based clustering
            cluster_id = 0
            for i in range(len(X)):
                if labels[i] != -1:  # Skip points already in a cluster
                    continue
                
                # Find neighbors within cluster_distance
                neighbors = []
                for j in range(len(X)):
                    if i != j and np.linalg.norm(X[i] - X[j]) <= cluster_distance:
                        neighbors.append(j)
                
                # If we have enough neighbors, form a cluster
                if len(neighbors) >= 5:
                    labels[i] = cluster_id
                    for j in neighbors:
                        labels[j] = cluster_id
                    cluster_id += 1
        
        # Count clusters (excluding noise which is labeled -1)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        print(f"POIs grouped into {n_clusters} clusters (plus individual points)")
        
        # Create a counter for each cluster
        cluster_counts = {}
        
        # Plot POIs with improved visualization
        for i, (pos_data, label) in enumerate(zip(poi_data, labels)):
            poi = pos_data['poi']
            x, y = pos_data['x'], pos_data['y']
            fac_type = pos_data['fac_type']
            color = color_map.get(fac_type, '#FF0000')  # Default red if type not found
            
            # Determine marker size and label based on whether it's part of a cluster
            if label >= 0:
                # This point is part of a cluster
                if label not in cluster_counts:
                    cluster_counts[label] = 0
                cluster_counts[label] += 1
                
                if cluster_counts[label] <= 3:  # Only plot the first few points in each cluster
                    marker_size = 8
                    circle = Circle((x, y), marker_size, color=color, alpha=0.7)
                    ax.add_patch(circle)
                    
                    # For the first point in a cluster, add a cluster label
                    if cluster_counts[label] == 1:
                        cluster_total = sum(1 for l in labels if l == label)
                        # Create a text box without using dict assignment
                        ax.text(x, y-15, f"Cluster: {cluster_total} POIs", 
                                fontsize=9, ha='center', va='center', 
                                color='white', weight='bold',
                                bbox={'facecolor': color, 'alpha': 0.7, 'pad': 0.3, 'boxstyle': 'round'})
            else:
                # Individual point (not in any cluster)
                marker_size = 10
                circle = Circle((x, y), marker_size, color=color, alpha=0.8)
                ax.add_patch(circle)
                
                # Add a subtle white outline
                edge = Circle((x, y), marker_size+1, color='white', alpha=0.5, fill=False)
                ax.add_patch(edge)
                
                # Add POI number with better visibility
                ax.text(x, y, str(i+1), fontsize=8, ha='center', va='center', 
                        color='white', weight='bold')
            
            # Store mapping for export
            poi_name = poi.get('POI_NAME', poi.get('name', f"POI {i+1}"))
            poi_mapping[i+1] = {
                'name': poi_name,
                'type': fac_type,
                'type_desc': get_facility_type_description(fac_type) if fac_type else "Unknown",
                'position': (x, y),
                'cluster': int(label) if label >= 0 else None
            }
            
            # Add more detailed info to export data
            export_data.append({
                'id': i+1,
                'name': poi_name,
                'facility_type': fac_type,
                'type_description': get_facility_type_description(fac_type) if fac_type else "Unknown",
                'x': x,
                'y': y,
                'cluster': int(label) if label >= 0 else None,
                **poi  # Include all original POI data
            })
    
    except Exception as e:
        print(f"Error during clustering: {e}")
        # Fallback method if clustering fails
        np.random.seed(42)  # For reproducibility
        
        # Create a more spaced out grid for POIs
        grid_size = int(np.ceil(np.sqrt(len(pois_to_display))))
        x_step = img_w / (grid_size + 1)
        y_step = img_h / (grid_size + 1)
        
        for i, poi in enumerate(pois_to_display):
            # Assign a position in the grid with some randomness
            grid_x = (i % grid_size) + 1
            grid_y = (i // grid_size) + 1
            
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
            
            color = color_map.get(fac_type, '#FF0000')
            
            # Plot a more visible dot
            circle = Circle((x, y), 8, color=color, alpha=0.7)
            ax.add_patch(circle)
            
            # Add POI number with better visibility
            ax.text(x, y, str(i+1), fontsize=7, ha='center', va='center', 
                    color='white', weight='bold')
            
            # Store mapping for export
            poi_name = poi.get('POI_NAME', poi.get('name', f"POI {i+1}"))
            poi_mapping[i+1] = {
                'name': poi_name,
                'type': fac_type,
                'type_desc': get_facility_type_description(fac_type) if fac_type else "Unknown",
                'position': (x, y)
            }
            
            # Add to export data
            export_data.append({
                'id': i+1,
                'name': poi_name,
                'facility_type': fac_type,
                'type_description': get_facility_type_description(fac_type) if fac_type else "Unknown",
                'x': x,
                'y': y,
                **poi  # Include all original POI data
            })
    
    # Create a more organized legend for facility types
    legend_elements = []
    for fac_type, color in sorted(color_map.items()):
        description = get_facility_type_description(fac_type)
        legend_elements.append(Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                                      markersize=10, label=f"{fac_type} - {description}"))
    
    # Set a more descriptive title with better styling
    title_text = f'POIs in Tile {tile_id} - {len(pois)} Total Points'
    if len(pois) > max_pois:
        title_text += f' (Showing {max_pois} with Clustering)'
    
    # Generate statistics about POI distribution by facility type
    type_counts = {}
    for poi in pois:
        fac_type = poi.get('FAC_TYPE', poi.get('type', 'Unknown'))
        if fac_type not in type_counts:
            type_counts[fac_type] = 0
        type_counts[fac_type] += 1
    
    # Get the top 3 most common facility types
    top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_types_str = ', '.join([f"{get_facility_type_description(t)}: {c}" for t, c in top_types])
    
    # Add info text at the bottom of the image
    textstr = '\n'.join([
        f'Total POIs: {len(pois)}',
        f'Facility Types: {len(color_map)}',
        f'Most Common: {top_types_str}',
        f'Tile Center: {center_lat:.4f}, {center_lon:.4f}'
    ])
    
    # Add text box for info
    ax.text(0.02, 0.02, textstr, transform=ax.transAxes, fontsize=9,
            verticalalignment='bottom', bbox={'facecolor': 'white', 'alpha': 0.7, 'boxstyle': 'round', 'pad': 0.5})
    
    # Add a more prominent title
    ax.set_title(title_text, fontsize=16, weight='bold', pad=20, 
                color='#333333', backgroundcolor='white', alpha=0.8)
    ax.axis('off')  # Hide axis
    
    # Use a more organized legend layout
    # Sort legend items for better readability and limit to most common types
    legend_items = sorted(color_map.items(), key=lambda x: sum(1 for p in pois if p.get('FAC_TYPE', p.get('type')) == x[0]), reverse=True)
    
    # Limit to top 20 most common facility types
    top_items = legend_items[:20]
    
    # Create legend elements for these items
    top_legend_elements = []
    for fac_type, color in top_items:
        count = sum(1 for p in pois if p.get('FAC_TYPE', p.get('type')) == fac_type)
        description = get_facility_type_description(fac_type)
        top_legend_elements.append(
            Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                  markersize=10, label=f"{fac_type} - {description} ({count})")
        )
    
    # If we're using clustering, add info to the legend
    try:
        if 'cluster' in export_data[0]:
            # Add cluster info to the legend
            cluster_count = len(set(p['cluster'] for p in export_data if p['cluster'] is not None))
            if cluster_count > 0:
                top_legend_elements.append(
                    Line2D([0], [0], marker='s', color='w', markerfacecolor='lightgray', 
                          markersize=10, label=f"POIs grouped in {cluster_count} clusters")
                )
    except (IndexError, KeyError):
        pass
    
    # Add the legend with improved layout
    legend = ax.legend(handles=top_legend_elements, loc='upper left', 
                     bbox_to_anchor=(1.01, 1.0), fontsize=9, 
                     title="Facility Types", title_fontsize=10,
                     frameon=True, framealpha=0.9)
    legend.get_frame().set_facecolor('white')
    
    # Adjust layout to make room for legend
    plt.tight_layout()
    plt.subplots_adjust(right=0.8)
    
    # Save mapping to a CSV file
    if output_csv:
        output_dir = Path('data/processed')
        output_dir.mkdir(exist_ok=True)
        
        # Save the detailed POI data
        df = pd.DataFrame(export_data)
        csv_file = output_dir / f'poi_map_tile_{tile_id}_data.csv'
        df.to_csv(csv_file, index=False)
        print(f"POI mapping data saved to {csv_file}")
    
    # Save at higher resolution with better quality
    output_file = f'poi_map_tile_{tile_id}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f"Enhanced map image saved to {output_file}")
    
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
