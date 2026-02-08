"""
Script to remove 'total_activity' key from all company.json files.

This script walks through all data/<company_id>/company.json files
and removes the 'total_activity' key from the metrics section
for each forecasting approach.
"""

import json
from pathlib import Path


def clean_company_json(json_path: Path) -> tuple[bool, str]:
    """
    Remove 'total_activity' from a single company.json file.
    
    Parameters
    ----------
    json_path : Path
        Path to the company.json file.
    
    Returns
    -------
    tuple[bool, str]
        (success, message)
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        modified = False
        
        # Check if this is a valid company.json with aggregated_metrics
        if 'aggregated_metrics' not in data:
            return False, "No aggregated_metrics found"
        
        # Iterate through each approach's metrics
        for approach_name, metrics in data['aggregated_metrics'].items():
            if 'total_activity' in metrics:
                del metrics['total_activity']
                modified = True
        
        if modified:
            # Write back to file with nice formatting
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True, "Removed total_activity"
        else:
            return False, "No total_activity found"
    
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Process all company.json files."""
    # Find the data directory
    data_dir = Path(__file__).parent.parent / "data"
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Find all company.json files
    json_files = list(data_dir.glob("*/company.json"))
    
    if not json_files:
        print(f"❌ No company.json files found in {data_dir}")
        return
    
    print(f"Found {len(json_files)} company.json files")
    print("-" * 60)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for json_path in sorted(json_files):
        company_id = json_path.parent.name
        success, message = clean_company_json(json_path)
        
        if success:
            print(f"✓ {company_id}: {message}")
            success_count += 1
        elif "Error" in message:
            print(f"✗ {company_id}: {message}")
            error_count += 1
        else:
            # Skipped (no total_activity or no aggregated_metrics)
            skip_count += 1
    
    print("-" * 60)
    print(f"Summary:")
    print(f"  ✓ Modified: {success_count}")
    print(f"  - Skipped:  {skip_count}")
    print(f"  ✗ Errors:   {error_count}")
    print(f"  Total:      {len(json_files)}")


if __name__ == "__main__":
    main()
