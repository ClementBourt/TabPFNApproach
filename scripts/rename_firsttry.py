#!/usr/bin/env python3
"""Migration script to rename 'FirstTry' to 'ProphetWorkflow' in company.json files.

This script:
1. Finds all company.json files under the data/ directory
2. Replaces "FirstTry" with "ProphetWorkflow" in version_name and description fields
3. Preserves the original file structure and formatting
4. Reports the number of files modified

Usage:
    uv run python scripts/rename_firsttry.py [--dry-run]
"""

import json
from pathlib import Path
from typing import Dict, Any
import argparse


def rename_firsttry_in_json(data: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
    """Rename 'FirstTry' to 'ProphetWorkflow' in JSON data.

    Parameters
    ----------
    data : Dict[str, Any]
        The JSON data from company.json

    Returns
    -------
    tuple[Dict[str, Any], bool]
        Updated data and a boolean indicating if any changes were made
    """
    modified = False
    
    if "forecast_versions" in data:
        for version in data["forecast_versions"]:
            # Update version_name field
            if version.get("version_name") == "FirstTry":
                version["version_name"] = "ProphetWorkflow"
                modified = True
            
            # Update description field
            if version.get("description") and "FirstTry" in version["description"]:
                version["description"] = version["description"].replace("FirstTry", "ProphetWorkflow")
                modified = True
    
    return data, modified


def process_company_json_files(data_dir: Path, dry_run: bool = False) -> tuple[int, int]:
    """Process all company.json files in the data directory.

    Parameters
    ----------
    data_dir : Path
        Path to the data directory
    dry_run : bool, optional
        If True, don't write changes, by default False

    Returns
    -------
    tuple[int, int]
        Number of files processed and number of files modified
    """
    company_json_files = list(data_dir.rglob("company.json"))
    total_files = len(company_json_files)
    modified_files = 0
    
    print(f"Found {total_files} company.json files")
    
    if dry_run:
        print("\n=== DRY RUN MODE - No files will be modified ===\n")
    
    for json_file in company_json_files:
        try:
            # Read the file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Rename FirstTry to ProphetWorkflow
            updated_data, modified = rename_firsttry_in_json(data)
            
            if modified:
                modified_files += 1
                print(f"{'[DRY RUN] Would modify' if dry_run else 'Modified'}: {json_file.relative_to(data_dir.parent)}")
                
                if not dry_run:
                    # Write back to file with proper formatting
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(updated_data, f, indent=2, ensure_ascii=False)
                        f.write('\n')  # Add trailing newline
        
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    return total_files, modified_files


def main() -> None:
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Rename 'FirstTry' to 'ProphetWorkflow' in company.json files"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without making changes (preview mode)'
    )
    args = parser.parse_args()
    
    # Get the data directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        return
    
    print(f"Processing company.json files in: {data_dir}\n")
    
    total, modified = process_company_json_files(data_dir, dry_run=args.dry_run)
    
    print(f"\n{'=== Summary (Dry Run) ===' if args.dry_run else '=== Summary ==='}")
    print(f"Total files processed: {total}")
    print(f"Files {'that would be ' if args.dry_run else ''}modified: {modified}")
    
    if args.dry_run and modified > 0:
        print("\nRun without --dry-run to apply changes")


if __name__ == "__main__":
    main()
