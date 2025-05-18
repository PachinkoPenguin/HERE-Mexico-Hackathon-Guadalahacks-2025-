# Satellite Imagery Functionality in POI Mapper

## Overview

The POI Mapper application now has the ability to display satellite imagery as the background for POI visualizations. This functionality uses the HERE Maps API to fetch satellite tiles that correspond to the map area being displayed.

## Requirements

To use the satellite imagery functionality, you need:

1. A HERE Maps API key with access to the Map Tile API
2. Python with the required dependencies installed (see `requirements.txt`)

## Usage

### With the main application

```bash
# Basic usage
python main.py map <TILE_ID> --satellite --api-key YOUR_API_KEY

# Example with zoom level
python main.py map 4815075 --satellite --api-key YOUR_API_KEY --zoom 18

# Example with clustering
python main.py map 4815075 --satellite --api-key YOUR_API_KEY --cluster-distance 30
```

### Setting up API key

You can provide your API key in several ways:

1. Command line option: `--api-key YOUR_API_KEY`
2. Environment variable: `export API_KEY=YOUR_API_KEY`
3. `.env` file in the project root:
   ```
   API_KEY=YOUR_API_KEY
   ```

## API URL Format

The HERE Maps API requires a specific URL format for satellite imagery requests:

```
https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{format}?style=satellite.day&size={size}&apiKey={api_key}
```

Note the correct parameter structure:
- Path components: `/{zoom}/{x}/{y}/{format}`
- First parameter after `?`: `style=satellite.day`
- Additional parameters separated by `&`: `&size=512&apiKey=YOUR_API_KEY`

## Fallback Mechanism

If the HERE Maps API is unavailable or rate-limited, the application will automatically fall back to a mock satellite image for development purposes. This allows you to continue developing and testing without API connectivity.

## Testing

You can test the satellite imagery functionality directly with:

```bash
python satellite_imagery_tile_request.py
```

This script will:
1. Convert coordinates to tile indices
2. Request the satellite image from the HERE Maps API
3. Save the image to `satellite_tile.png`
4. Output the WKT polygon representing the tile bounds

## Troubleshooting

If you encounter issues with satellite imagery:

1. Check your API key is valid and has sufficient quota
2. Verify network connectivity to the HERE Maps API
3. Try different zoom levels (10-20)
4. Look for error messages indicating rate limiting or other API issues

For any persistent issues, refer to the [HERE Maps API documentation](https://developer.here.com/documentation/map-tile/dev_guide/index.html).
