#!/usr/bin/env python3
"""
Script to extract trajectories for resolved instances from SWE evaluation results.

This script:
1. Reads report.json files from evaluation logs
2. Extracts resolved instance IDs
3. Copies corresponding trajectory folders to a separate directory
"""

import json
import os
import shutil
import argparse
from pathlib import Path
from typing import List, Set, Dict


def load_resolved_ids_from_json(json_file_path: str) -> Set[str]:
    """Load resolved instance IDs from a JSON file."""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Handle both the paste.txt format and report.json format
        if 'ids_resolved' in data:
            return set(data['ids_resolved'])
        elif 'resolved' in data and isinstance(data['resolved'], list):
            return set(data['resolved'])
        else:
            print(f"Warning: Could not find resolved IDs in {json_file_path}")
            return set()
    except Exception as e:
        print(f"Error reading {json_file_path}: {e}")
        return set()


def load_resolved_ids_from_report(report_path: str) -> Set[str]:
    """Load resolved instance IDs from a report.json file."""
    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        resolved_ids = set()
        
        # Check if it's a list of results
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get('resolved', False):
                    resolved_ids.add(item.get('instance_id', ''))
        # Check if it's a dict with results
        elif isinstance(data, dict):
            if 'results' in data:
                for item in data['results']:
                    if isinstance(item, dict) and item.get('resolved', False):
                        resolved_ids.add(item.get('instance_id', ''))
            # Handle the format from paste.txt
            elif 'ids_resolved' in data:
                return set(data['ids_resolved'])
        
        # Remove empty strings
        resolved_ids.discard('')
        return resolved_ids
        
    except Exception as e:
        print(f"Error reading report {report_path}: {e}")
        return set()


def find_trajectory_folders(trajectories_base: str, resolved_ids: Set[str], updated_tools: bool = False) -> Dict[str, str]:
    """Find trajectory folders for resolved instance IDs."""
    trajectory_map = {}

    subset_pattern = "subset*_2000" if not updated_tools  else "subset*_2000_updated_tools" 
    
    # Search through all subset folders
    for subset_dir in Path(trajectories_base).glob(subset_pattern):
        if not subset_dir.is_dir():
            continue
            
        print(f"Searching in {subset_dir.name}...")
        
        for folder in subset_dir.iterdir():
            if not folder.is_dir():
                continue
                
            folder_name = folder.name
            
            # Check if any resolved ID matches this folder name
            for resolved_id in resolved_ids:
                if resolved_id in folder_name:
                    trajectory_map[resolved_id] = str(folder)
                    print(f"  Found: {resolved_id} -> {folder_name}")
                    break
    
    return trajectory_map


def copy_trajectories(trajectory_map: Dict[str, str], output_dir: str):
    """Copy trajectory folders to output directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\nCopying {len(trajectory_map)} trajectory folders to {output_dir}...")
    
    for resolved_id, trajectory_path in trajectory_map.items():
        source_path = Path(trajectory_path)
        dest_path = output_path / source_path.name
        
        try:
            if dest_path.exists():
                print(f"  Skipping {source_path.name} (already exists)")
                continue
                
            shutil.copytree(source_path, dest_path)
            print(f"  Copied: {source_path.name}")
        except Exception as e:
            print(f"  Error copying {source_path.name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Extract resolved instance trajectories")
    parser.add_argument("--logs-dir", default="logs/run_evaluation", 
                       help="Path to evaluation logs directory")
    parser.add_argument("--trajectories-dir", default="trajectories",
                       help="Path to trajectories directory")
    parser.add_argument("--output-dir", default="resolved_trajectories",
                       help="Output directory for copied trajectories")
    parser.add_argument("--resolved-ids-file", 
                       help="Optional: JSON file with resolved IDs (like paste.txt)")
    parser.add_argument("--updated-tools", 
                        action="store_true",
                        default=False,
                        help="if to parse from updated tools")
    
    args = parser.parse_args()
    
    logs_path = Path(args.logs_dir)
    trajectories_path = Path(args.trajectories_dir)
    
    if not logs_path.exists():
        print(f"Error: Logs directory {logs_path} does not exist")
        return
        
    if not trajectories_path.exists():
        print(f"Error: Trajectories directory {trajectories_path} does not exist")
        return
    
    # Collect all resolved IDs
    all_resolved_ids = set()

    subset_pattern = "subset*_2000" if not args.updated_tools  else "subset*_2000_updated_tools" 
    
    # If a specific file with resolved IDs is provided, use that
    if args.resolved_ids_file:
        print(f"Loading resolved IDs from {args.resolved_ids_file}...")
        all_resolved_ids.update(load_resolved_ids_from_json(args.resolved_ids_file))
    else:
        # Otherwise, scan all report.json files
        print("Scanning report.json files for resolved instances...")
        
        for subset_dir in logs_path.glob(subset_pattern):
            if not subset_dir.is_dir():
                continue
                
            report_file = subset_dir / "report.json"
            if report_file.exists():
                print(f"Processing {subset_dir.name}/report.json...")
                resolved_ids = load_resolved_ids_from_report(str(report_file))
                all_resolved_ids.update(resolved_ids)
                print(f"  Found {len(resolved_ids)} resolved instances")
    
    print(f"\nTotal resolved instances found: {len(all_resolved_ids)}")
    
    if not all_resolved_ids:
        print("No resolved instances found. Exiting.")
        return
    
    # Find corresponding trajectory folders
    print("\nSearching for trajectory folders...")
    trajectory_map = find_trajectory_folders(str(trajectories_path), all_resolved_ids, args.updated_tools)
    
    print(f"\nFound trajectory folders for {len(trajectory_map)} out of {len(all_resolved_ids)} resolved instances")
    
    # Show missing trajectories
    missing = all_resolved_ids - set(trajectory_map.keys())
    if missing:
        print(f"\nMissing trajectory folders for {len(missing)} instances:")
        for missing_id in sorted(missing)[:10]:  # Show first 10
            print(f"  {missing_id}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")
    
    # Copy trajectory folders
    if trajectory_map:
        copy_trajectories(trajectory_map, args.output_dir)
        print(f"\nDone! Copied trajectories to {args.output_dir}")
    else:
        print("No trajectory folders found to copy.")


if __name__ == "__main__":
    main()