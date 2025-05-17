#!/usr/bin/env python3
from poi295_validator import POI295Validator
import pandas as pd
import geopandas as gpd
import os

def print_section(title):
    """Print a section title with dividers for better readability"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

# Create validator
validator = POI295Validator()

print_section("VALIDATOR TEST WITH LOWERCASE COLUMN NAMES")
# Test with our fixed test files 
test_violations = validator.find_violations_in_tile("TEST_FIXED")
print(f"Found {len(test_violations)} violations")

if test_violations:
    # Print the first violation for debugging
    print("\nFirst violation details:")
    for key, value in test_violations[0].items():
        if key != 'poi_data':
            print(f"{key}: {value}")
        else:
            print(f"{key}: {len(value)} keys")
else:
    print("\nNo violations found in test data")

# Test with a POI that will trigger a violation
print_section("VALIDATOR TEST WITH VIOLATION CASE")

# Debug: Check the files directly
print("Debug: Checking test files directly")
try:
    poi_file = "/home/ada/Development/Personal/Guadalahacks_2025/data/POIs/POI_VIOLATION.csv"
    street_file = "/home/ada/Development/Personal/Guadalahacks_2025/data/STREETS_NAV/SREETS_NAV_VIOLATION.geojson"
    
    print(f"POI file exists: {os.path.exists(poi_file)}")
    print(f"Street file exists: {os.path.exists(street_file)}")
    
    if os.path.exists(poi_file) and os.path.exists(street_file):
        pois = pd.read_csv(poi_file)
        streets = gpd.read_file(street_file)
        
        print("\nPOI data:")
        print(pois)
        
        print("\nStreets data:")
        print(streets)
except Exception as e:
    print(f"Error checking files: {e}")

# Now run the validator
print_section("RUNNING VALIDATOR ON VIOLATION TEST CASE")
violation_test = validator.find_violations_in_tile("VIOLATION")
print(f"Found {len(violation_test)} violations")

if violation_test:
    # Print the violation details
    print("\nViolation details:")
    for key, value in violation_test[0].items():
        if key != 'poi_data':
            print(f"{key}: {value}")
        else:
            print(f"{key}: {len(value)} keys")
    
    print_section("TESTING CORRECTION FUNCTIONALITY")
    # Test automatic correction
    validator.violations = violation_test
    correction_summary = validator.apply_corrections()
    print(f"\nApplied {correction_summary['total']} corrections:")
    for key, value in correction_summary.items():
        if key != 'total':
            print(f"  - {key}: {value}")
    
    # Check if the corrected file was created
    corrected_poi_file = "/home/ada/Development/Personal/Guadalahacks_2025/data/processed/corrected_POI_VIOLATION.csv"
    if os.path.exists(corrected_poi_file):
        print("\nCorrected POI file created successfully:")
        corrected_pois = pd.read_csv(corrected_poi_file)
        print(corrected_pois)
    else:
        print("\nWarning: Corrected POI file was not created")
else:
    print("\nNo violations found in violation test data - this is unexpected")

print_section("TEST COMPLETE")
