#!/usr/bin/env python3
"""
Before/After comparison tool for POI Visualization improvements
"""
import os
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

def create_comparison_visualization(original_img, improved_img, output_name="visualization_comparison"):
    """
    Create a side-by-side comparison of the original and improved visualizations
    """
    # Check if both images exist
    if not os.path.exists(original_img):
        print(f"Original image not found: {original_img}")
        return
    
    if not os.path.exists(improved_img):
        print(f"Improved image not found: {improved_img}")
        return
    
    # Load the images
    img_original = Image.open(original_img)
    img_improved = Image.open(improved_img)
    
    # Create figure for comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # Display original image
    ax1.imshow(np.array(img_original))
    ax1.set_title("Original Visualization", fontsize=16)
    ax1.axis('off')
    
    # Display improved image
    ax2.imshow(np.array(img_improved))
    ax2.set_title("Improved Visualization", fontsize=16)
    ax2.axis('off')
    
    # Set overall title
    fig.suptitle("POI Visualization Before/After Comparison", fontsize=22, weight='bold')
    plt.tight_layout()
    
    # Save comparison
    output_file = f"{output_name}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Comparison saved to {output_file}")
    
    return fig

if __name__ == "__main__":
    # For demonstration, we'll create a copy of the original visualization first
    import sys
    import shutil
    
    if len(sys.argv) < 3:
        print("Usage: python comparison.py <original_image> <improved_image> [output_name]")
        sys.exit(1)
        
    original_img = sys.argv[1]
    improved_img = sys.argv[2]
    output_name = sys.argv[3] if len(sys.argv) > 3 else "visualization_comparison"
    
    create_comparison_visualization(original_img, improved_img, output_name)
