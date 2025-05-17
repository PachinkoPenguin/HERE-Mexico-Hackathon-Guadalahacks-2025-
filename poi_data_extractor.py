#!/usr/bin/env python3
import os
import csv
import json
import pandas as pd
import glob
from pathlib import Path

def extract_all_poi_data(output_format='json'):
    """
    Extract all POI data from all CSV files in the POIs directory
    and save it to a single file in the specified format.
    
    Parameters:
    output_format (str): Format to save the data ('json', 'csv', or 'excel')
    
    Returns:
    str: Path to the output file
    """
    poi_dir = Path('data/POIs')
    output_dir = Path('data/processed')
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Get all POI CSV files
    poi_files = list(poi_dir.glob('POI_*.csv'))
    print(f"Found {len(poi_files)} POI files")
    
    # Read facility types mapping for better descriptions
    facility_types = {}
    try:
        with open('data/docs/POI_Facility_Types.csv', 'r') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader)
            for row in reader:
                if len(row) >= 2:
                    facility_types[row[0]] = row[1]
    except Exception as e:
        print(f"Warning: Could not read facility types: {e}")
    
    # Initialize a list to store all POI data
    all_pois = []
    
    # Process each POI file
    for poi_file in poi_files:
        tile_id = poi_file.stem.split('_')[1]
        print(f"Processing {poi_file.name}...")
        
        try:
            # Read the CSV file using pandas for more robust parsing
            df = pd.read_csv(poi_file, low_memory=False)
            
            # Add tile_id as a column
            df['TILE_ID'] = tile_id
            
            # Add facility type description if available
            if facility_types:
                df['FAC_TYPE_DESC'] = df['FAC_TYPE'].astype(str).map(facility_types).fillna('Unknown')
            
            # Convert DataFrame to list of dictionaries
            file_pois = df.to_dict('records')
            
            # Add to the master list
            all_pois.extend(file_pois)
            
        except Exception as e:
            print(f"Error processing {poi_file.name}: {e}")
    
    print(f"Total POIs extracted: {len(all_pois)}")
    
    # Save all POI data to the specified format
    if output_format.lower() == 'json':
        output_file = output_dir / 'all_pois.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_pois, f, indent=2, ensure_ascii=False)
    
    elif output_format.lower() == 'csv':
        output_file = output_dir / 'all_pois.csv'
        # Convert back to DataFrame and save as CSV
        pd.DataFrame(all_pois).to_csv(output_file, index=False)
    
    elif output_format.lower() == 'excel':
        output_file = output_dir / 'all_pois.xlsx'
        # Convert back to DataFrame and save as Excel
        pd.DataFrame(all_pois).to_excel(output_file, index=False)
    
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
    
    print(f"All POI data saved to {output_file}")
    return str(output_file)

def extract_tile_poi_data(tile_id, output_format='json'):
    """
    Extract POI data for a specific tile ID
    
    Parameters:
    tile_id (int or str): The tile ID to extract data for
    output_format (str): Format to save the data ('json', 'csv', or 'excel')
    
    Returns:
    str: Path to the output file
    """
    poi_file = Path(f'data/POIs/POI_{tile_id}.csv')
    output_dir = Path('data/processed')
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    if not poi_file.exists():
        print(f"POI file for tile {tile_id} not found: {poi_file}")
        return None
    
    # Read facility types mapping for better descriptions
    facility_types = {}
    try:
        with open('data/docs/POI_Facility_Types.csv', 'r') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader)
            for row in reader:
                if len(row) >= 2:
                    facility_types[row[0]] = row[1]
    except Exception as e:
        print(f"Warning: Could not read facility types: {e}")
    
    print(f"Processing {poi_file.name}...")
    
    try:
        # Read the CSV file using pandas for more robust parsing
        df = pd.read_csv(poi_file, low_memory=False)
        
        # Add tile_id as a column
        df['TILE_ID'] = tile_id
        
        # Add facility type description if available
        if facility_types:
            df['FAC_TYPE_DESC'] = df['FAC_TYPE'].astype(str).map(facility_types).fillna('Unknown')
        
        # Convert DataFrame to list of dictionaries
        pois = df.to_dict('records')
        
        print(f"Found {len(pois)} POIs in tile {tile_id}")
        
        # Save POI data to the specified format
        if output_format.lower() == 'json':
            output_file = output_dir / f'poi_tile_{tile_id}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(pois, f, indent=2, ensure_ascii=False)
        
        elif output_format.lower() == 'csv':
            output_file = output_dir / f'poi_tile_{tile_id}.csv'
            # Save as CSV
            df.to_csv(output_file, index=False)
        
        elif output_format.lower() == 'excel':
            output_file = output_dir / f'poi_tile_{tile_id}.xlsx'
            # Save as Excel
            df.to_excel(output_file, index=False)
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        print(f"POI data for tile {tile_id} saved to {output_file}")
        return str(output_file)
    
    except Exception as e:
        print(f"Error processing {poi_file.name}: {e}")
        return None
    """
    Generate a summary of the POI data, grouping by facility type
    and providing counts and other insights.
    
    Parameters:
    input_file (str): Path to the input file (if None, the function will generate it)
    
    Returns:
    str: Path to the summary file
    """
    if input_file is None:
        # Generate the all_pois file if it doesn't exist
        input_file = extract_all_poi_data(output_format='json')
    
    output_dir = Path('data/processed')
    output_dir.mkdir(exist_ok=True)
    
    # Read the POI data
    if input_file.endswith('.json'):
        with open(input_file, 'r', encoding='utf-8') as f:
            all_pois = json.load(f)
        df = pd.DataFrame(all_pois)
    elif input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    elif input_file.endswith('.xlsx'):
        df = pd.read_excel(input_file)
    else:
        raise ValueError(f"Unsupported input format: {input_file}")
    
    # Generate summaries
    summary = {
        'total_pois': len(df),
        'tiles': df['TILE_ID'].nunique(),
        'facility_types': df.groupby(['FAC_TYPE', 'FAC_TYPE_DESC']).size().reset_index(name='count').to_dict('records'),
        'top_names': df['POI_NAME'].value_counts().head(20).to_dict(),
        'poi_per_tile': df.groupby('TILE_ID').size().to_dict()
    }
    
    # Save summary to JSON
    summary_file = output_dir / 'poi_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"POI summary saved to {summary_file}")
    return str(summary_file)


def create_poi_lookup_table():
    """
    Create a lookup table that maps POI IDs to their information.
    This allows quick access to POI data by ID.
    
    Returns:
    str: Path to the lookup table file
    """
    # First, make sure we have the combined data
    all_pois_file = Path('data/processed/all_pois.json')
    if not all_pois_file.exists():
        extract_all_poi_data(output_format='json')
    
    # Read the POI data
    with open(all_pois_file, 'r', encoding='utf-8') as f:
        all_pois = json.load(f)
    
    # Create a dictionary mapping POI_ID to POI information
    lookup_table = {}
    for poi in all_pois:
        poi_id = poi.get('POI_ID')
        if poi_id:
            lookup_table[str(poi_id)] = poi
    
    # Save the lookup table
    output_dir = Path('data/processed')
    output_file = output_dir / 'poi_lookup.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lookup_table, f, indent=2, ensure_ascii=False)
    
    print(f"POI lookup table saved to {output_file}")
    return str(output_file)


def list_available_tiles():
    """
    List all available tile IDs in the POIs directory
    """
    poi_dir = Path('data/POIs')
    
    # Get all POI CSV files
    poi_files = list(poi_dir.glob('POI_*.csv'))
    
    # Extract tile IDs
    tile_ids = [file.stem.split('_')[1] for file in poi_files]
    
    print(f"Found {len(tile_ids)} tiles:")
    for tile_id in sorted(tile_ids):
        print(f"  - {tile_id}")
    
    return tile_ids


def show_menu():
    """
    Display an interactive menu for the POI Data Extractor
    """
    while True:
        print("\nPOI Data Extractor Menu")
        print("----------------------")
        print("1. Extract data for all POIs")
        print("2. Extract data for a specific tile")
        print("3. Generate POI summary")
        print("4. Create POI lookup table")
        print("5. List available tiles")
        print("6. View visualization for a tile (launches poi_mapper.py)")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-6): ")
        
        if choice == '1':
            formats = ['json', 'csv']
            for fmt in formats:
                try:
                    extract_all_poi_data(output_format=fmt)
                except Exception as e:
                    print(f"Error extracting data in {fmt} format: {e}")
        
        elif choice == '2':
            tile_id = input("Enter the tile ID: ")
            formats = ['json', 'csv']
            for fmt in formats:
                try:
                    extract_tile_poi_data(tile_id, output_format=fmt)
                except Exception as e:
                    print(f"Error extracting data for tile {tile_id} in {fmt} format: {e}")
        
        elif choice == '3':
            generate_poi_summary()
        
        elif choice == '4':
            create_poi_lookup_table()
        
        elif choice == '5':
            list_available_tiles()
        
        elif choice == '6':
            tile_id = input("Enter the tile ID for visualization: ")
            # Launch poi_mapper.py with the specified tile ID
            import subprocess
            try:
                print(f"\nLaunching poi_mapper.py for tile {tile_id}...")
                subprocess.run([sys.executable, "poi_mapper.py"], input=f"{tile_id}\n".encode(), check=True)
            except Exception as e:
                print(f"Error launching poi_mapper.py: {e}")
        
        elif choice == '0':
            print("Exiting POI Data Extractor")
            break
        
        else:
            print("Invalid choice. Please enter a number between 0 and 6.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Command line arguments provided
        if sys.argv[1] == "--all":
            print("POI Data Extractor")
            print("------------------")
            
            print("\nExtracting all POI data...")
            all_pois_file = extract_all_poi_data(output_format='json')
            
            # Also create CSV version for convenience
            extract_all_poi_data(output_format='csv')
            
            print("\nGenerating POI summary...")
            summary_file = generate_poi_summary(all_pois_file)
            
            print("\nCreating POI lookup table...")
            lookup_file = create_poi_lookup_table()
            
            print("\nDone! Files created:")
            print(f"- {all_pois_file}")
            print(f"- {all_pois_file.replace('.json', '.csv')}")
            print(f"- {summary_file}")
            print(f"- {lookup_file}")
        
        elif sys.argv[1] == "--tile" and len(sys.argv) > 2:
            # Extract data for a specific tile
            tile_id = sys.argv[2]
            extract_tile_poi_data(tile_id, output_format='json')
            extract_tile_poi_data(tile_id, output_format='csv')
        
        elif sys.argv[1] == "--list":
            # List available tiles
            list_available_tiles()
        
        else:
            print("Usage:")
            print("  python poi_data_extractor.py                  # Interactive menu")
            print("  python poi_data_extractor.py --all            # Extract all POI data")
            print("  python poi_data_extractor.py --tile <tile_id> # Extract data for a specific tile")
            print("  python poi_data_extractor.py --list           # List available tiles")
    
    else:
        # No command line arguments, show interactive menu
        show_menu()
