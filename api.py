# api.py - Flask backend to serve the React app and provide API endpoints
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import os
import json
import subprocess
import sys
import importlib.util
import traceback
from compararPOI import verificar_poi_desde_json, verificar_poi_desde_csv_corregido
import finalcode

app = Flask(__name__, static_folder='Page/dist')
CORS(app)

# Development mode flag
is_dev_mode = os.environ.get('FLASK_DEBUG') == '1' or not os.path.exists('Page/dist')

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if is_dev_mode:
        # In development mode, redirect to the Vite dev server
        return redirect('http://127.0.0.1:5174')
    
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# API endpoints for running scripts
@app.route('/api/verify-poi', methods=['POST'])
def api_verify_poi():
    try:
        data = request.json
        poi_type = data.get('type')
        poi_data = data.get('data')
        
        if poi_type == 'json':
            result = verificar_poi_desde_json(poi_data)
        elif poi_type == 'csv':
            csv_line = poi_data.get('csv_line')
            nodos = poi_data.get('nodos')
            link_id = poi_data.get('link_id')  # Optional link_id for auto-matching

            # If nodos are not provided but link_id is, try to find the matching street
            if not nodos and link_id and 'street_file' in poi_data:
                street_file = poi_data.get('street_file')
                street_path = os.path.join("STREETS_NAV", street_file)
                
                if os.path.exists(street_path):
                    with open(street_path, 'r') as f:
                        streets_data = json.load(f)
                        
                    # Find the street with matching link_id
                    for feature in streets_data.get('features', []):
                        if feature.get('properties', {}).get('link_id') == link_id or str(feature.get('properties', {}).get('link_id')) == str(link_id):
                            nodos = feature.get('geometry', {}).get('coordinates', [])
                            break
            
            if not nodos:
                return jsonify({"error": "No street geometry (nodos) provided or found"}), 400
                
            result = verificar_poi_desde_csv_corregido(csv_line, nodos)
        else:
            return jsonify({"error": "Unsupported POI type"}), 400
            
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in verify-poi endpoint: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/api/get-tiles', methods=['GET'])
def api_get_tiles():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        zoom = int(request.args.get('zoom', 16))
        
        tile_x, tile_y = finalcode.lat_lon_to_tile(lat, lon, zoom)
        return jsonify({
            "tile_x": tile_x,
            "tile_y": tile_y,
            "zoom": zoom
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/list-poi-files', methods=['GET'])
def api_list_poi_files():
    try:
        poi_files = []
        for filename in os.listdir("POIs"):
            if filename.endswith(".csv"):
                poi_files.append(filename)
        return jsonify({"files": poi_files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/list-street-files', methods=['GET'])
def api_list_street_files():
    try:
        nav_files = []
        for filename in os.listdir("STREETS_NAV"):
            if filename.endswith(".geojson"):
                nav_files.append(filename)
        return jsonify({"files": nav_files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/read-poi-file', methods=['GET'])
def api_read_poi_file():
    try:
        filename = request.args.get('filename')
        if not filename or '../' in filename:  # Basic path traversal protection
            return jsonify({"error": "Invalid filename"}), 400
            
        filepath = os.path.join("POIs", filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
            
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        return jsonify({
            "filename": filename,
            "lines": lines
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/read-street-file', methods=['GET'])
def api_read_street_file():
    try:
        filename = request.args.get('filename')
        if not filename or '../' in filename:  # Basic path traversal protection
            return jsonify({"error": "Invalid filename"}), 400
            
        filepath = os.path.join("STREETS_NAV", filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        return jsonify({
            "filename": filename,
            "data": data
        })
    except Exception as e:
        app.logger.error(f"Error reading street file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/run-script', methods=['POST'])
def api_run_script():
    """Fallback endpoint for directly running a Python script"""
    try:
        data = request.json
        script_name = data.get('script')
        args = data.get('args', [])
        
        if not script_name or '../' in script_name:  # Basic path traversal protection
            return jsonify({"error": "Invalid script name"}), 400
            
        if not os.path.exists(script_name):
            return jsonify({"error": "Script not found"}), 404
        
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_name] + args,
            capture_output=True,
            text=True
        )
        
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exitCode": result.returncode
        })
    except Exception as e:
        app.logger.error(f"Error running script: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/find-matches', methods=['GET'])
def api_find_matches():
    """Find POIs that have matching streets with the same LINK_ID"""
    try:
        poi_file = request.args.get('poi_file')
        street_file = request.args.get('street_file')
        limit = int(request.args.get('limit', 15))  # Limit results to avoid overwhelming response
        
        if not poi_file or not street_file:
            return jsonify({"error": "Both poi_file and street_file parameters are required"}), 400
            
        # Validate filenames
        if '../' in poi_file or '../' in street_file:
            return jsonify({"error": "Invalid filename"}), 400
            
        poi_path = os.path.join("POIs", poi_file)
        street_path = os.path.join("STREETS_NAV", street_file)
        
        if not os.path.exists(poi_path) or not os.path.exists(street_path):
            return jsonify({"error": "File not found"}), 404
            
        # Read street file to extract link_ids
        with open(street_path, 'r') as f:
            street_data = json.load(f)
            
        link_ids = set()
        for feature in street_data.get('features', []):
            if feature.get('properties') and 'link_id' in feature.get('properties'):
                link_ids.add(str(feature.get('properties').get('link_id')))
        
        # Read POI file to find POIs with matching link_ids
        matches = []
        with open(poi_path, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            fields = line.strip().split(',')
            if len(fields) > 1:
                link_id = fields[1]
                if link_id in link_ids:
                    poi_name = fields[5] if len(fields) > 5 else "Unknown"
                    poi_id = fields[0] if len(fields) > 0 else "Unknown"
                    side = fields[13] if len(fields) > 13 else "R"
                    perc = fields[22] if len(fields) > 22 else (fields[20] if len(fields) > 20 else "")
                    
                    matches.append({
                        "poi_id": poi_id,
                        "link_id": link_id,
                        "name": poi_name,
                        "side": side,
                        "perc": perc,
                        "csv_line": line
                    })
                    
                    if len(matches) >= limit:
                        break
                        
        return jsonify({
            "poi_file": poi_file,
            "street_file": street_file,
            "match_count": len(matches),
            "matches": matches
        })
    except Exception as e:
        app.logger.error(f"Error finding matches: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/api/popular-pois', methods=['GET'])
def api_popular_pois():
    """Get popular POI categories and examples from the files"""
    try:
        # Map of POI types to their descriptions based on the FAC_TYPE column
        poi_types = {
            "4013": "City Center",
            "5800": "Restaurant",
            "7538": "Auto Service",
            "9535": "Convenience Store",
            "9567": "Food Shop",
            "9988": "Stationery Store",
            "7997": "Sports Center",
            "8211": "School/Educational Institution",
            "9992": "Religious Place"
        }
        
        # Get a sample of POIs for each type
        results = {}
        poi_dir = "POIs"
        
        # Check if directory exists
        if not os.path.exists(poi_dir):
            return jsonify({"error": f"POI directory not found: {poi_dir}"}), 404
            
        # Get list of POI files
        poi_files = [f for f in os.listdir(poi_dir) if f.endswith('.csv')]
        
        # Limit to first 5 files for efficiency
        sample_files = poi_files[:5] if len(poi_files) > 5 else poi_files
        
        # For each file, extract some popular POIs
        for poi_file in sample_files:
            file_path = os.path.join(poi_dir, poi_file)
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                fields = line.strip().split(',')
                if len(fields) < 6:
                    continue
                    
                poi_type = fields[4] if len(fields) > 4 else ""
                poi_name = fields[5] if len(fields) > 5 else ""
                link_id = fields[1] if len(fields) > 1 else ""
                poi_id = fields[0] if len(fields) > 0 else ""
                
                if not poi_type or not poi_name or not link_id:
                    continue
                
                # Skip empty or unnamed POIs
                if not poi_name.strip():
                    continue
                    
                # If this is a recognized POI type, add to results
                if poi_type in poi_types:
                    if poi_type not in results:
                        results[poi_type] = {
                            "type_name": poi_types[poi_type],
                            "examples": []
                        }
                    
                    # Add this POI as an example if we don't have too many already
                    if len(results[poi_type]["examples"]) < 5:
                        results[poi_type]["examples"].append({
                            "poi_id": poi_id,
                            "link_id": link_id,
                            "name": poi_name,
                            "file": poi_file
                        })
        
        # Convert to a list for easier consumption by frontend
        formatted_results = []
        for poi_type, data in results.items():
            formatted_results.append({
                "type_id": poi_type,
                "type_name": data["type_name"],
                "examples": data["examples"]
            })
            
        return jsonify({
            "popular_poi_types": formatted_results
        })
    except Exception as e:
        app.logger.error(f"Error getting popular POIs: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/api/poi-stats', methods=['GET'])
def api_poi_stats():
    """Get statistics about the POI dataset"""
    try:
        # Parameters
        poi_file = request.args.get('poi_file')
        street_file = request.args.get('street_file')
        
        # Validate filenames if provided
        if poi_file and '../' in poi_file:
            return jsonify({"error": "Invalid POI filename"}), 400
            
        if street_file and '../' in street_file:
            return jsonify({"error": "Invalid street filename"}), 400
            
        # Statistics containers
        stats = {
            "total_pois": 0,
            "poi_types": {},
            "poi_with_links": 0,
            "poi_without_links": 0,
            "street_coverage": {},
            "poi_by_side": {"L": 0, "R": 0, "B": 0, "Unknown": 0}
        }
        
        # Process all POI files or just the specified one
        poi_files = []
        if poi_file:
            poi_files = [poi_file]
        else:
            poi_files = [f for f in os.listdir("POIs") if f.endswith('.csv')]
            
        # Load street data if specified
        street_link_ids = set()
        if street_file:
            street_path = os.path.join("STREETS_NAV", street_file)
            if os.path.exists(street_path):
                with open(street_path, 'r') as f:
                    street_data = json.load(f)
                for feature in street_data.get('features', []):
                    if 'properties' in feature and 'link_id' in feature['properties']:
                        street_link_ids.add(str(feature['properties']['link_id']))
        
        # Process POI files
        for poi_file in poi_files:
            file_path = os.path.join("POIs", poi_file)
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                fields = line.strip().split(',')
                if len(fields) < 5:  # Skip invalid/header lines
                    continue
                    
                stats["total_pois"] += 1
                
                # Extract POI type
                poi_type = fields[4] if len(fields) > 4 else "Unknown"
                poi_type_name = "Unknown"
                
                # Map facility type to name if it's a common one
                poi_types_map = {
                    "4013": "City Center",
                    "5800": "Restaurant",
                    "7538": "Auto Service",
                    "9535": "Convenience Store",
                    "9567": "Food Shop",
                    "9988": "Stationery Store",
                    "7997": "Sports Center",
                    "8211": "School/Educational Institution",
                    "9992": "Religious Place"
                }
                
                if poi_type in poi_types_map:
                    poi_type_name = poi_types_map[poi_type]
                
                # Count by POI type
                if poi_type not in stats["poi_types"]:
                    stats["poi_types"][poi_type] = {
                        "count": 0,
                        "name": poi_type_name
                    }
                stats["poi_types"][poi_type]["count"] += 1
                
                # Check for link_id
                link_id = fields[1] if len(fields) > 1 else ""
                if link_id:
                    stats["poi_with_links"] += 1
                    
                    # Check if this link exists in the street file
                    if street_file and street_link_ids:
                        if link_id in street_link_ids:
                            if link_id not in stats["street_coverage"]:
                                stats["street_coverage"][link_id] = 0
                            stats["street_coverage"][link_id] += 1
                else:
                    stats["poi_without_links"] += 1
                
                # Count by side of street
                side = fields[13] if len(fields) > 13 else ""
                if side == "L":
                    stats["poi_by_side"]["L"] += 1
                elif side == "R":
                    stats["poi_by_side"]["R"] += 1
                elif side == "B":
                    stats["poi_by_side"]["B"] += 1
                else:
                    stats["poi_by_side"]["Unknown"] += 1
        
        # Calculate percentages and prepare final response
        if stats["total_pois"] > 0:
            stats["percent_with_links"] = round((stats["poi_with_links"] / stats["total_pois"]) * 100, 2)
        else:
            stats["percent_with_links"] = 0
            
        # Sort POI types by count for easier consumption
        sorted_poi_types = []
        for poi_type, data in stats["poi_types"].items():
            sorted_poi_types.append({
                "type_id": poi_type,
                "type_name": data["name"],
                "count": data["count"],
                "percentage": round((data["count"] / stats["total_pois"]) * 100, 2) if stats["total_pois"] > 0 else 0
            })
        
        sorted_poi_types.sort(key=lambda x: x["count"], reverse=True)
        stats["poi_types_summary"] = sorted_poi_types
        del stats["poi_types"]
        
        # For street coverage, calculate how many streets have POIs
        if street_file:
            stats["streets_with_pois"] = len(stats["street_coverage"])
            stats["streets_total"] = len(street_link_ids)
            stats["streets_coverage_percent"] = round((stats["streets_with_pois"] / stats["streets_total"]) * 100, 2) if stats["streets_total"] > 0 else 0
            
            # Keep only top streets by POI count
            top_streets = sorted(stats["street_coverage"].items(), key=lambda x: x[1], reverse=True)[:20]
            stats["top_streets_by_poi_count"] = [{"link_id": s[0], "poi_count": s[1]} for s in top_streets]
            del stats["street_coverage"]
            
        return jsonify({
            "stats": stats,
            "poi_files_analyzed": len(poi_files),
            "street_file": street_file if street_file else "None"
        })
    except Exception as e:
        app.logger.error(f"Error getting POI stats: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/api/batch-verify-pois', methods=['POST'])
def api_batch_verify_pois():
    """Verify multiple POIs at once and return the results"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        poi_items = data.get('poi_items', [])
        street_file = data.get('street_file')
        
        if not poi_items or not street_file:
            return jsonify({"error": "Both poi_items and street_file are required"}), 400
            
        # Validate street filename
        if '../' in street_file:
            return jsonify({"error": "Invalid street filename"}), 400
            
        street_path = os.path.join("STREETS_NAV", street_file)
        if not os.path.exists(street_path):
            return jsonify({"error": f"Street file not found: {street_file}"}), 404
            
        # Load street data once to avoid repeated loading
        with open(street_path, 'r') as f:
            street_data = json.load(f)
            
        # Process each POI
        results = []
        for item in poi_items:
            csv_line = item.get('csv_line')
            link_id = item.get('link_id')
            
            if not csv_line or not link_id:
                continue
                
            # Find the matching street segment for this POI
            nodos = None
            for feature in street_data.get('features', []):
                if feature.get('properties', {}).get('link_id') == link_id or str(feature.get('properties', {}).get('link_id')) == str(link_id):
                    nodos = feature.get('geometry', {}).get('coordinates', [])
                    break
                    
            if not nodos:
                results.append({
                    "poi_id": item.get('poi_id'),
                    "error": "No matching street geometry found",
                    "success": False
                })
                continue
                
            # Verify this POI
            result = verificar_poi_desde_csv_corregido(csv_line, nodos)
            result["poi_id"] = item.get('poi_id')
            result["success"] = True
            results.append(result)
            
        return jsonify({
            "batch_results": results,
            "total_processed": len(results),
            "success_count": sum(1 for r in results if r.get("success", False))
        })
    except Exception as e:
        app.logger.error(f"Error in batch-verify-pois endpoint: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
