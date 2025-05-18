#!/usr/bin/env python3
"""
Multi-Tile Visualization Helper for POI Visualization
This script helps create combined visualizations from multiple tiles
"""
import os
import argparse
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
from PIL import Image
import pandas as pd

def create_multi_tile_visualization(tile_ids, output_name=None, layout=None):
    """
    Create a multi-tile visualization by combining individual tile images
    
    Parameters:
    -----------
    tile_ids : list
        List of tile IDs to combine
    output_name : str, optional
        Name for the output file (without extension)
    layout : tuple, optional
        Grid layout as (rows, cols). If None, will be determined automatically
    """
    # Check if the tile images exist
    available_tiles = []
    for tile_id in tile_ids:
        tile_img_path = f'poi_map_tile_{tile_id}.png'
        if os.path.exists(tile_img_path):
            available_tiles.append((tile_id, tile_img_path))
        else:
            print(f"Warning: Image for tile {tile_id} not found.")
    
    if not available_tiles:
        print("No tile images found. Please generate them first with 'python main.py map <tile_id>'")
        return
    
    n_tiles = len(available_tiles)
    
    # Determine layout if not provided
    if not layout:
        # Calculate a reasonable grid layout
        if n_tiles <= 2:
            layout = (1, n_tiles)
        elif n_tiles <= 4:
            layout = (2, 2)
        elif n_tiles <= 6:
            layout = (2, 3)
        elif n_tiles <= 9:
            layout = (3, 3)
        elif n_tiles <= 12:
            layout = (3, 4)
        else:
            layout = (4, (n_tiles + 3) // 4)
    
    rows, cols = layout
    
    # Create figure with GridSpec for more control
    fig = plt.figure(figsize=(cols*8, rows*6), constrained_layout=True)
    gs = GridSpec(rows, cols, figure=fig)
    
    # Load and display each tile
    print(f"Creating combined visualization of {n_tiles} tiles...")
    
    tile_summary = pd.DataFrame(columns=['Tile ID', 'POI Count', 'Top Facility Types'])
    
    for i, (tile_id, img_path) in enumerate(available_tiles):
        # Calculate position in grid
        row = i // cols
        col = i % cols
        
        # Create subplot
        ax = fig.add_subplot(gs[row, col])
        
        # Load image
        img = Image.open(img_path)
        ax.imshow(np.array(img))
        
        # Remove axes for cleaner look
        ax.axis('off')
        
        # Try to load the data file to get summary info
        data_file = f'data/processed/poi_map_tile_{tile_id}_data.csv'
        if os.path.exists(data_file):
            try:
                df = pd.read_csv(data_file)
                poi_count = len(df)
                
                # Get top facility types
                if 'facility_type' in df.columns:
                    top_types = df['facility_type'].value_counts().head(3).index.tolist()
                    top_types_str = ', '.join([str(t) for t in top_types])
                elif 'type' in df.columns:
                    top_types = df['type'].value_counts().head(3).index.tolist()
                    top_types_str = ', '.join([str(t) for t in top_types])
                else:
                    top_types_str = "Unknown"
                
                # Add to summary
                tile_summary.loc[i] = [tile_id, poi_count, top_types_str]
            except Exception as e:
                print(f"Error reading data file for tile {tile_id}: {e}")
                tile_summary.loc[i] = [tile_id, "Unknown", "Unknown"]
    
    # Set the overall title
    if output_name:
        title = f"Combined POI Visualization - {output_name}"
    else:
        title = f"Combined POI Visualization of {n_tiles} Tiles"
    
    fig.suptitle(title, fontsize=24, weight='bold', y=0.98)
    
    # Save the figure
    output_file = f"combined_poi_visualization_{output_name or 'multi_tile'}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Multi-tile visualization saved to {output_file}")
    
    # Generate a summary CSV
    summary_file = f"combined_poi_summary_{output_name or 'multi_tile'}.csv"
    tile_summary.to_csv(summary_file, index=False)
    print(f"Tile summary saved to {summary_file}")
    
    return fig

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create multi-tile POI visualizations')
    parser.add_argument('tile_ids', type=str, nargs='+', help='List of tile IDs to include')
    parser.add_argument('--name', type=str, help='Name for the output file')
    parser.add_argument('--rows', type=int, default=0, help='Number of rows in the grid layout')
    parser.add_argument('--cols', type=int, default=0, help='Number of columns in the grid layout')
    
    args = parser.parse_args()
    
    # Determine layout
    layout = None
    if args.rows > 0 and args.cols > 0:
        layout = (args.rows, args.cols)
    
    # Create visualization
    create_multi_tile_visualization(args.tile_ids, args.name, layout)
