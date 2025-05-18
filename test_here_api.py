#!/usr/bin/env python3
"""
HERE Maps Satellite API Key Checker

This script tests your HERE Maps API key to see if it can retrieve satellite imagery.
"""
import os
import sys
import requests
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

# Load API key from .env file if it exists
load_dotenv()
API_KEY = os.getenv('API_KEY', '')

def test_here_maps_api(api_key, coordinate=None):
    """Test if a HERE Maps API key can retrieve satellite imagery."""
    
    if not api_key:
        print("❌ No API key provided. Please provide an API key.")
        return False
    
    # Use default coordinates (Mexico City) or provided coordinates
    if coordinate:
        lat, lon = coordinate
    else:
        lat, lon = 19.432608, -99.133209  # Mexico City
    
    # Parameters for the request
    zoom = 17
    tile_format = 'png'
    
    # Calculate tile x,y from lat/lon
    x, y = lat_lon_to_tile(lat, lon, zoom)
    
    # Create URL for HERE Maps satellite tile
    url = f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size=512&apiKey={api_key}'
    
    print(f"Testing HERE Maps API with key: {api_key[:3]}...{api_key[-3:]}")
    print(f"Coordinates: {lat}, {lon} (Tile: {x}, {y}, Zoom: {zoom})")
    print(f"URL: {url.replace(api_key, 'YOUR_API_KEY_HIDDEN')}")
    
    try:
        response = requests.get(url, timeout=15)
        
        # Check response status
        if response.status_code == 200:
            # Check if we got an image
            content_type = response.headers.get('Content-Type', '')
            
            if 'image' in content_type.lower():
                print("✅ SUCCESS! API key is valid and returned satellite imagery.")
                
                # Save the image
                output_file = 'satellite_test.png'
                with open(output_file, 'wb') as file:
                    file.write(response.content)
                print(f"Satellite image saved to {output_file}")
                
                # Display the image
                try:
                    img = Image.open(BytesIO(response.content))
                    plt.figure(figsize=(10, 10))
                    plt.imshow(img)
                    plt.title(f"Satellite image for {lat}, {lon}")
                    plt.axis('off')
                    plt.show()
                except Exception as e:
                    print(f"Error displaying image: {e}")
                
                return True
            else:
                print(f"❌ ERROR: API returned non-image content: {content_type}")
                print(f"Response: {response.text[:200]}")
        else:
            print(f"❌ ERROR: API request failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
            if response.status_code == 401 or response.status_code == 403:
                print("This suggests your API key is invalid or doesn't have access to satellite imagery.")
            elif response.status_code == 429:
                print("You have exceeded your rate limit. Wait a while or use a different API key.")
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    return False

def lat_lon_to_tile(lat, lon, zoom):
    """Convert latitude and longitude to tile coordinates."""
    import math
    
    # Ensure latitude is within bounds
    lat = max(min(lat, 85.05112878), -85.05112878)
    
    # Calculate number of tiles at this zoom level
    n = 2.0 ** zoom
    
    # Calculate x and y tile indices
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    
    return x, y

if __name__ == "__main__":
    # Check if API key is provided as an argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = API_KEY
        if not api_key:
            print("No API key found. Please provide an API key as an argument or in a .env file.")
            print("Usage: python test_here_api.py YOUR_API_KEY")
            print("       or create a .env file with API_KEY=YOUR_API_KEY")
            sys.exit(1)
    
    # Optional: Allow specifying coordinates
    coordinate = None
    if len(sys.argv) > 3:
        try:
            lat = float(sys.argv[2])
            lon = float(sys.argv[3])
            coordinate = (lat, lon)
        except ValueError:
            print("Invalid coordinates. Using default coordinates.")
    
    # Test the API key
    test_here_maps_api(api_key, coordinate)
