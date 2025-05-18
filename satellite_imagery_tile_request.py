import requests
import math
from dotenv import load_dotenv
import os

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
    
    # Calculate x and y tile indices (WebMercator formula)
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2.0 * n)
    
    return (x, y)

def tile_coords_to_lat_lon(x, y, zoom):
    n = 2.0 ** zoom
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1-2 * y/n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def get_tile_bounds(x, y, zoom):
    lat1, lon1 = tile_coords_to_lat_lon(x,y,zoom)
    lat2, lon2 = tile_coords_to_lat_lon(x+1, y, zoom)
    lat3, lon3 = tile_coords_to_lat_lon(x+1,y+1,zoom)
    lat4, lon4 = tile_coords_to_lat_lon(x,y+1,zoom)
    return (lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4)

def create_wkt_polygon(bounds):
    (lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4) = bounds
    wkt = f"POLYGON(({lon1} {lat1}, {lon2} {lat2}, {lon3} {lat3}, {lon4} {lat4}, {lon1} {lat1}))"
    return wkt



def get_satellite_tile(lat, lon, zoom, tile_format, api_key):
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
    
    Returns:
    --------
    str
        WKT polygon representing the bounds of the tile
    """
    # Convert lat/lon to tile coordinates
    x, y = lat_lon_to_tile(lat, lon, zoom)
    
    # Set tile size (512 is recommended by HERE API)
    tile_size = 512

    # Construct the URL for the map tile API - IMPORTANT: parameters must come after ? and be separated by &
    url = f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size={tile_size}&apiKey={api_key}'
    
    # Print the URL for debugging (with API key redacted)
    print(f"Requesting URL: {url.replace(api_key, 'API_KEY_HIDDEN')}")

    # Make the request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the tile to a file
        with open(f'satellite_tile.{tile_format}', 'wb') as file:
            file.write(response.content)
        print('Tile saved successfully.')
    else:
        print(f'Failed to retrieve tile. Status code: {response.status_code}')

    bounds = get_tile_bounds(x,y, zoom)
    wkt_polygon = create_wkt_polygon(bounds)
    return wkt_polygon

##########################################################
### EXECUTION
##########################################################
# Define the parameters for the tile request
api_key = API_KEY
latitude = 51.94347 
longitude = 8.51692 
zoom_level = 20  # Zoom level
tile_size = 512  # Tile size in pixels - also used in get_satellite_tile function
tile_format = 'png'  # Tile format

# Execute request and save tile
wkt_bounds = get_satellite_tile(latitude,longitude,zoom_level,tile_format,api_key)
print(wkt_bounds)

