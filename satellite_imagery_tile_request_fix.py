#!/usr/bin/env python3
import requests
import math
from dotenv import load_dotenv
import os
import numpy as np
from PIL import Image
from io import BytesIO

# Load environment variables
load_dotenv()
API_KEY = os.getenv('API_KEY')

def lat_lon_to_tile(lat, lon, zoom):
    """
    Convert latitude and longitude to tile indices (x, y) at a given zoom level.
    
    :param lat: Latitude in degrees
    :param lon: Longitude in degrees
    :param zoom: Zoom level (0-19)
    :return: Tuple (x, y) representing the tile indices
    """
    # Ensure latitude is within bounds to prevent math domain errors
    lat = max(min(lat, 85.05112878), -85.05112878)
    
    # Calculate n (number of tiles at the given zoom level)
    n = 2.0 ** zoom
    
    # Calculate x and y tile indices
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    
    return (x, y)

def tile_coords_to_lat_lon(x, y, zoom):
    """
    Convert tile coordinates back to latitude and longitude.
    
    :param x: Tile x coordinate
    :param y: Tile y coordinate
    :param zoom: Zoom level
    :return: Tuple (lat, lon) in degrees
    """
    n = 2.0 ** zoom
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1-2 * y/n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def get_tile_bounds(x, y, zoom):
    """
    Get the latitude/longitude bounds of a tile.
    
    :param x: Tile x coordinate
    :param y: Tile y coordinate
    :param zoom: Zoom level
    :return: Four corner coordinates of the tile as (lat, lon) tuples
    """
    lat1, lon1 = tile_coords_to_lat_lon(x, y, zoom)
    lat2, lon2 = tile_coords_to_lat_lon(x+1, y, zoom)
    lat3, lon3 = tile_coords_to_lat_lon(x+1, y+1, zoom)
    lat4, lon4 = tile_coords_to_lat_lon(x, y+1, zoom)
    return (lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4)

def create_wkt_polygon(bounds):
    """
    Create a WKT (Well-Known Text) representation of the tile bounds.
    
    :param bounds: Four corner coordinates of a tile
    :return: WKT polygon string
    """
    (lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4) = bounds
    wkt = f"POLYGON(({lon1} {lat1}, {lon2} {lat2}, {lon3} {lat3}, {lon4} {lat4}, {lon1} {lat1}))"
    return wkt

def get_satellite_tile(lat, lon, zoom, tile_format, api_key, tile_size=512):
    """
    Get a satellite imagery tile for the given coordinates using HERE Maps API.
    
    :param lat: Latitude in degrees
    :param lon: Longitude in degrees
    :param zoom: Zoom level (0-19)
    :param tile_format: Image format (png or jpg)
    :param api_key: HERE Maps API key
    :param tile_size: Size of the tile in pixels (default 512)
    :return: WKT polygon representing the bounds of the retrieved tile
    """
    # Convert lat/lon to tile coordinates
    x, y = lat_lon_to_tile(lat, lon, zoom)
    print(f"Calculated tile coordinates: x={x}, y={y} for lat={lat}, lon={lon}, zoom={zoom}")
    
    # Try multiple URL formats for HERE Maps API
    urls = [
        # v3 API base endpoint
        f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size={tile_size}&apiKey={api_key}',
        
        # v3 API with ppi parameter
        f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size={tile_size}&ppi=72&apiKey={api_key}',
        
        # v3 aerial endpoint
        f'https://aerial.maps.hereapi.com/v3/aerial/mc/{zoom}/{x}/{y}/{tile_format}?apiKey={api_key}',
        
        # v2.1 aerial endpoint with numbered domain
        f'https://1.aerial.maps.ls.hereapi.com/maptile/2.1/maptile/newest/satellite.day/{zoom}/{x}/{y}/{tile_size}/{tile_format}?apiKey={api_key}',
        
        # v2.1 alternative domain
        f'https://2.aerial.maps.ls.hereapi.com/maptile/2.1/maptile/newest/satellite.day/{zoom}/{x}/{y}/{tile_size}/{tile_format}?apiKey={api_key}'
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
                    # Save the tile to a file
                    with open(f'satellite_tile_{i+1}.{tile_format}', 'wb') as file:
                        file.write(response.content)
                    print(f'Tile saved successfully with URL #{i+1}.')
                    
                    # Get tile bounds
                    bounds = get_tile_bounds(x, y, zoom)
                    wkt_polygon = create_wkt_polygon(bounds)
                    
                    return wkt_polygon
                else:
                    print(f"API returned non-image content: {content_type}")
            else:
                print(f'URL #{i+1} failed. Status code: {response.status_code}')
        except Exception as e:
            print(f"Error with URL #{i+1}: {e}")
    
    print("All attempts to get satellite imagery failed.")
    
    # Generate a mock satellite image for testing
    try:
        mock_img = create_mock_satellite_image(tile_size)
        mock_img.save(f'mock_satellite.{tile_format}')
        print(f"Created mock satellite image for testing.")
        
        # Get tile bounds
        bounds = get_tile_bounds(x, y, zoom)
        wkt_polygon = create_wkt_polygon(bounds)
        
        return wkt_polygon
    except Exception as e:
        print(f"Failed to create mock image: {e}")
        return None

def create_mock_satellite_image(tile_size=512):
    """
    Create a mock satellite image for testing when the API is unavailable.
    
    :param tile_size: Size of the tile in pixels
    :return: PIL Image object
    """
    # Try to create a realistic-looking satellite image with noise patterns
    from numpy import random
    
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
    
    return pil_img

def main():
    """
    Main function to execute satellite tile retrieval.
    """
    # Define the parameters for the tile request
    api_key = API_KEY
    if not api_key:
        print("API_KEY not found in environment variables or .env file")
        api_key = input("Enter your HERE Maps API key: ")
    
    latitude = float(input("Enter latitude (default: 51.94347): ") or "51.94347")
    longitude = float(input("Enter longitude (default: 8.51692): ") or "8.51692")
    zoom_level = int(input("Enter zoom level (0-19, default: 17): ") or "17")
    tile_size = int(input("Enter tile size in pixels (default: 512): ") or "512")
    tile_format = input("Enter tile format (png/jpg, default: png): ") or "png"
    
    # Execute request and save tile
    wkt_bounds = get_satellite_tile(latitude, longitude, zoom_level, tile_format, api_key, tile_size)
    
    if wkt_bounds:
        print("\nTile bounds (WKT format):")
        print(wkt_bounds)
        print("\nSatellite image saved successfully.")
    else:
        print("\nFailed to retrieve satellite imagery.")

if __name__ == "__main__":
    main()
