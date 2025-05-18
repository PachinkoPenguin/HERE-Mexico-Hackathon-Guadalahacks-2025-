# Satellite Imagery Guide for Guadalahacks 2025 POI Mapper

## Getting Real Satellite Imagery Working

The POI Mapper can display POIs on top of satellite imagery, but you'll need a valid HERE Maps API key. The current implementation has been fixed to use the correct URL format, but you still need valid credentials.

### Steps to Enable Satellite View:

1. **Get a HERE Maps API Key**:
   - Sign up for a HERE Developer account at [https://developer.here.com/](https://developer.here.com/)
   - Create a new project and get your API key
   - Make sure your key has access to the Maps API (Raster Tiles)

2. **Set up your API Key**:
   - Create a `.env` file in your project root with:
     ```
     API_KEY=your_here_maps_api_key_here
     ```
   - Or pass the key directly with the `--api-key` parameter

3. **Run with Satellite Imagery**:
   ```bash
   python3 main.py map 4815075 --satellite
   ```
   
   Or with a direct API key:
   ```bash
   python3 main.py map 4815075 --satellite --api-key your_here_maps_api_key_here
   ```

## Troubleshooting

### "Unable to retrieve satellite imagery. Using fallback image..."

This message appears when:
1. The API key is invalid or missing
2. There are connection issues to the HERE Maps servers
3. The API rate limit has been exceeded

The application will automatically fall back to a generated mock satellite image that looks like a satellite view.

### "Successfully retrieved satellite imagery for the map background."

This message suggests that either:
1. Real satellite imagery was retrieved, or
2. The mock satellite image was successfully generated

To confirm real satellite imagery is being used, look for:
- Detailed terrain features in the image
- Roads that match real-world geography
- Success messages like "Satellite tile retrieved successfully with URL #X"

## URL Format Fix

The satellite imagery API URL format was previously incorrect. It has been fixed to use the correct structure:

```python
# CORRECT URL format ✅
url = f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size={tile_size}&apiKey={api_key}'
```

Remember that query parameters must come after the `?` and additional parameters must be separated by `&`.

## Testing Your API Key

You can test your HERE Maps API key directly using the `satellite_imagery_tile_request.py` script:

```bash
# Edit the script to include your API key or use a .env file
python3 satellite_imagery_tile_request.py
```

A successful run will save a satellite tile to `satellite_tile.png`.

## Default Map Mode

If you don't have an API key or don't need satellite imagery, you can run the tool without the `--satellite` flag to get a standard map visualization:

```bash
python3 main.py map 4815075
```

This will create a styled map with grid lines and POI visualizations without requiring a HERE Maps API key.
