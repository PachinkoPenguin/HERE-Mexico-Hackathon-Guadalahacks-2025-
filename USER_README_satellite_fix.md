# filepath: /home/ada/Development/Personal/Guadalahacks_2025/USER_README_satellite_fix.md

# HERE Maps Satellite Imagery Fix

This document explains the fix for the HERE Maps satellite imagery API URL structure issue.

## The Issue

The original URL structure in the script had issues with query parameter formatting:

```python
# INCORRECT URL Structure ❌
url = f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}&style=satellite.day&size={tile_size}?apiKey={api_key}'
```

The issue is that query parameters are incorrectly placed. The above URL mixes `&` and `?` in the wrong order.

## The Fix

The correct URL structure should be:

```python
# CORRECT URL Structure ✅
url = f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size={tile_size}&apiKey={api_key}'
```

Key points:
1. The URL path should be: `/{zoom}/{x}/{y}/{format}`
2. The first parameter must be preceded by `?`
3. Additional parameters must be separated by `&`

## Working Example

```python
def get_satellite_tile(lat, lon, zoom, tile_format, api_key, size=512):
    """Get a satellite imagery tile from HERE Maps API"""
    # Get tile coordinates
    x, y = lat_lon_to_tile(lat, lon, zoom)
    
    # Construct the URL with correct parameter order
    url = f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size={size}&apiKey={api_key}'
    
    # Make the request
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Handle the successful response
        # ...
```

## Testing Your Fix

You can run the fixed script to verify:

```bash
python3 satellite_imagery_tile_request_user_fix.py
```

## Alternative API Endpoints

If you're still having trouble with satellite imagery, try these alternative endpoints:

```python
# v3 aerial endpoint
f'https://aerial.maps.hereapi.com/v3/aerial/mc/{zoom}/{x}/{y}/{tile_format}?apiKey={api_key}'

# v2.1 aerial endpoint with numbered domain
f'https://1.aerial.maps.ls.hereapi.com/maptile/2.1/maptile/newest/satellite.day/{zoom}/{x}/{y}/{tile_size}/{tile_format}?apiKey={api_key}'
```

Remember to always use the `?` for the first parameter and `&` for additional parameters!
