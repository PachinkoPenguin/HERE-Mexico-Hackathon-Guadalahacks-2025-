#!/usr/bin/env python3
import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from poi_data_extractor import extract_all_poi_data, extract_tile_poi_data
from poi_mapper import plot_pois_on_map, find_tile_center
from poi295_validator import POI295Validator

def main():
    """
    Main function for the Guadalahacks 2025 POI295 validation tool
    """
    parser = argparse.ArgumentParser(description='HERE POI295 Validation Tool - Guadalahacks 2025')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract POI data')
    extract_parser.add_argument('--tile', type=str, help='Tile ID to extract data for (optional)')
    extract_parser.add_argument('--format', type=str, choices=['json', 'csv', 'excel'], default='json',
                                help='Output format (json, csv, or excel)')
    
    # Map command
    map_parser = subparsers.add_parser('map', help='Generate POI map')
    map_parser.add_argument('tile', type=str, help='Tile ID to generate map for')
    map_parser.add_argument('--satellite', action='store_true', help='Include satellite imagery')
    map_parser.add_argument('--api-key', type=str, help='HERE API key for satellite imagery')
    map_parser.add_argument('--zoom', type=int, default=15, help='Zoom level for satellite imagery')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate POI295 violations')
    validate_parser.add_argument('--tile', type=str, help='Tile ID to validate (optional, defaults to all tiles)')
    validate_parser.add_argument('--report', action='store_true', help='Generate validation report')
    validate_parser.add_argument('--visualize', action='store_true', help='Visualize sample violations')
    validate_parser.add_argument('--correct', action='store_true', help='Apply automatic corrections')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Process commands
    if args.command == 'extract':
        if args.tile:
            output_file = extract_tile_poi_data(args.tile, args.format)
        else:
            output_file = extract_all_poi_data(args.format)
        print(f"Data extracted to {output_file}")
    
    elif args.command == 'map':
        # Get center coordinates for the tile
        try:
            tile_info = find_tile_center(args.tile)
            if not tile_info:
                print(f"Tile {args.tile} not found in the HERE_L11_Tiles.geojson file.")
                print("Please check the tile ID and try again.")
                return
            
            center_coords = tile_info['center']
            bounds = tile_info['bounds']
            
            # Generate the map
            api_key_env = os.environ.get('HERE_API_KEY', '')
            api_key_to_use = args.api_key if args.api_key else api_key_env
            
            if not api_key_to_use and args.satellite:
                # Check for API key in .env file
                try:
                    if os.path.exists('.env'):
                        with open('.env', 'r') as env_file:
                            for line in env_file:
                                if line.startswith('HERE_API_KEY='):
                                    api_key_to_use = line.split('=')[1].strip()
                                    break
                except Exception as e:
                    print(f"Error reading .env file: {e}")
                
                if not api_key_to_use:
                    print("Warning: No HERE API key provided. Satellite imagery won't be available.")
                    print("Use --api-key option or set HERE_API_KEY environment variable.")
            
            fig, export_data = plot_pois_on_map(
                args.tile,
                api_key=api_key_to_use,
                zoom_level=args.zoom
            )
            
            # Display the map
            plt.show()
            
            # Output file path is based on the plot_pois_on_map function's naming
            output_file = f'poi_map_tile_{args.tile}.png'
            if os.path.exists(output_file):
                print(f"Map generated and saved to {output_file}")
                
                # Also mention the data file
                data_file = f'data/processed/poi_map_tile_{args.tile}_data.csv'
                if os.path.exists(data_file):
                    print(f"POI data saved to {data_file}")
            
        except Exception as e:
            print(f"Error generating map: {e}")
            import traceback
            traceback.print_exc()
    
    elif args.command == 'validate':
        validator = POI295Validator()
        
        if args.tile:
            # Validate a specific tile
            violations = validator.find_violations_in_tile(args.tile)
            print(f"Found {len(violations)} POI295 violations in tile {args.tile}")
        else:
            # Validate all tiles
            violations = validator.find_all_violations()
            print(f"Found {len(violations)} POI295 violations across all tiles")
        
        if args.correct and violations:
            # Apply corrections
            correction_summary = validator.apply_corrections()
            print(f"Applied {correction_summary['total']} corrections:")
            print(f"  - POIs deleted: {correction_summary['delete_poi']}")
            print(f"  - POIs updated: {correction_summary['update_poi']}")
            print(f"  - Links updated: {correction_summary['update_link']}")
        
        if args.report and violations:
            # Generate report
            report_file = validator.generate_report()
            print(f"Report generated: {report_file}")
        
        if args.visualize and violations:
            # Visualize sample violations
            validator.visualize_sample_violations()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
