#!/usr/bin/env python3
"""
SWE Experiment Results Aggregator

This script processes experiment log directories to calculate total resolved instances
and collect all resolved instance IDs from report.json files.
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, List, Set

def load_report_json(file_path: str) -> Dict:
    """Load and parse a report.json file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def find_report_files(base_directory: str) -> List[str]:
    """Find all report.json files in subset directories."""
    # Pattern to match subset directories
    pattern = os.path.join(base_directory, "subset*_*/report.json")
    return glob.glob(pattern)

def aggregate_results(base_directory: str) -> Dict:
    """
    Aggregate results from all report.json files in the base directory.
    
    Args:
        base_directory: Path to the directory containing subset folders
        
    Returns:
        Dictionary with aggregated statistics and resolved instance IDs
    """
    report_files = find_report_files(base_directory)
    
    if not report_files:
        print(f"No report.json files found in {base_directory}")
        return {}
    
    # Initialize aggregation variables
    total_resolved = 0
    total_unresolved = 0
    total_instances = 0
    all_resolved_ids = set()
    all_unresolved_ids = set()
    subset_results = []
    
    print(f"Found {len(report_files)} report.json files:")
    
    for report_file in sorted(report_files):
        print(f"  Processing: {report_file}")
        
        # Extract subset name from path
        subset_name = os.path.basename(os.path.dirname(report_file))
        
        # Load the report
        report_data = load_report_json(report_file)
        
        if not report_data:
            continue
            
        # Extract data from report
        resolved = report_data.get('resolved', 0)
        unresolved = report_data.get('unresolved', 0)
        total = report_data.get('total', 0)
        resolved_ids = report_data.get('ids_resolved', [])
        unresolved_ids = report_data.get('ids_unresolved', [])
        
        # Add to totals
        total_resolved += resolved
        total_unresolved += unresolved
        total_instances += total
        all_resolved_ids.update(resolved_ids)
        all_unresolved_ids.update(unresolved_ids)
        
        # Store subset result
        subset_results.append({
            'subset': subset_name,
            'resolved': resolved,
            'unresolved': unresolved,
            'total': total,
            'resolved_ids_count': len(resolved_ids),
            'unresolved_ids_count': len(unresolved_ids)
        })
        
        print(f"    {subset_name}: {resolved} resolved, {unresolved} unresolved, {total} total")
    
    # Calculate resolution rate
    resolution_rate = (total_resolved / total_instances * 100) if total_instances > 0 else 0
    
    # Check for overlapping IDs (should not happen in a proper experiment)
    overlapping_ids = all_resolved_ids.intersection(all_unresolved_ids)
    
    return {
        'summary': {
            'total_resolved': total_resolved,
            'total_unresolved': total_unresolved,
            'total_instances': total_instances,
            'resolution_rate_percent': round(resolution_rate, 2),
            'unique_resolved_ids': len(all_resolved_ids),
            'unique_unresolved_ids': len(all_unresolved_ids),
            'overlapping_ids_count': len(overlapping_ids)
        },
        'resolved_instance_ids': sorted(list(all_resolved_ids)),
        'unresolved_instance_ids': sorted(list(all_unresolved_ids)),
        'overlapping_ids': sorted(list(overlapping_ids)) if overlapping_ids else [],
        'subset_breakdown': subset_results
    }

def save_results(results: Dict, output_file: str = None):
    """Save aggregated results to a JSON file."""
    if output_file is None:
        output_file = "aggregated_results.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")

def print_summary(results: Dict):
    """Print a formatted summary of the results."""
    if not results:
        print("No results to display.")
        return
    
    summary = results['summary']
    
    print("\n" + "="*60)
    print("SWE EXPERIMENT RESULTS SUMMARY")
    print("="*60)
    print(f"Total Resolved Instances:    {summary['total_resolved']:,}")
    print(f"Total Unresolved Instances:  {summary['total_unresolved']:,}")
    print(f"Total Instances:             {summary['total_instances']:,}")
    print(f"Resolution Rate:             {summary['resolution_rate_percent']:.2f}%")
    print(f"Unique Resolved IDs:         {summary['unique_resolved_ids']:,}")
    print(f"Unique Unresolved IDs:       {summary['unique_unresolved_ids']:,}")
    
    if summary['overlapping_ids_count'] > 0:
        print(f"⚠️  Overlapping IDs:          {summary['overlapping_ids_count']:,}")
        print("   (IDs that appear in both resolved and unresolved lists)")
    
    print("\nSubset Breakdown:")
    print("-" * 60)
    for subset in results['subset_breakdown']:
        rate = (subset['resolved'] / subset['total'] * 100) if subset['total'] > 0 else 0
        print(f"{subset['subset']:<20} {subset['resolved']:>6}/{subset['total']:<6} ({rate:>5.1f}%)")

def main():
    """Main function to run the aggregation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Aggregate SWE experiment results from report.json files')
    parser.add_argument('directory', nargs='?', default='.', 
                       help='Base directory containing subset folders (default: current directory)')
    parser.add_argument('-o', '--output', default='aggregated_results.json',
                       help='Output file for detailed results (default: aggregated_results.json)')
    parser.add_argument('--no-save', action='store_true',
                       help='Don\'t save results to file, only print summary')
    parser.add_argument('--ids-only', action='store_true',
                       help='Only print resolved instance IDs (one per line)')
    
    args = parser.parse_args()
    
    # Convert to absolute path
    base_dir = os.path.abspath(args.directory)
    
    if not os.path.exists(base_dir):
        print(f"Error: Directory '{base_dir}' does not exist.")
        return 1
    
    print(f"Aggregating results from: {base_dir}")
    
    # Aggregate results
    results = aggregate_results(base_dir)
    
    if not results:
        print("No results found.")
        return 1
    
    # Handle different output modes
    if args.ids_only:
        # Just print resolved IDs, one per line
        for instance_id in results['resolved_instance_ids']:
            print(instance_id)
    else:
        # Print summary
        print_summary(results)
        
        # Save detailed results unless requested not to
        if not args.no_save:
            save_results(results, args.output)
    
    return 0

if __name__ == "__main__":
    exit(main())