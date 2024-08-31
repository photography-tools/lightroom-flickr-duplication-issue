"""
lr-deep-fix.py: Lightroom-Flickr Deep Fix Utility

This script processes the results from lr-deep-audit.py to generate commands for fixing
mismatches between a Lightroom catalog and a Flickr set. It handles timestamp matches
and filename matches, generating appropriate merge.py and add-set.py commands.

Usage:
    python lr-deep-fix.py

Requirements:
    - Python 3.6+
    - Input file: 'lr_deep_audit_results.json' (output from lr-deep-audit.py)
    - secrets.json file with:
        {
            "api_key": "your_flickr_api_key",
            "api_secret": "your_flickr_api_secret",
            "lrcat_file_path": "/path/to/your/lightroom_catalog.lrcat",
            "set_id": "your_flickr_set_id"
        }

Output:
    - fix_commands.log: Log file containing merge.py and add-set.py commands

Functionality:
    1. Process timestamp_matches and filename_matches from lr_deep_audit_results.json
    2. For single matches:
       - Generate merge.py command with --goner (old remoteId) and --keeper (current flickr_id)
    3. For multiple matches:
       - Select the match with the highest view count for merge.py command
       - Generate add-set.py commands for other matches to add them to 'Potential Duplicates' set

Note: This script assumes the existence of merge.py and add-set.py utilities.
"""

import json
import os
from typing import List, Dict, Any

def load_audit_results() -> Dict[str, Any]:
    """Load the audit results from the JSON file."""
    with open('lr_deep_audit_results.json', 'r') as f:
        return json.load(f)

def process_matches(matches: List[Dict[str, Any]], match_type: str) -> List[str]:
    """Process matches and generate appropriate commands."""
    commands = []
    for match in matches:
        lr_remote_id = match['lr_remote_id']
        flickr_matches = match['flickr_matches']

        if len(flickr_matches) == 1:
            flickr_id = flickr_matches[0]['flickr_id']
            commands.append(f"python merge.py --goner {lr_remote_id} --keeper {flickr_id} --missing --force")
        elif len(flickr_matches) > 1:
            # Sort matches by view count in descending order
            sorted_matches = sorted(flickr_matches, key=lambda x: x['flickr_views'], reverse=True)

            # Use the match with the highest view count for merge.py
            top_match = sorted_matches[0]
            commands.append(f"python merge.py --goner {lr_remote_id} --keeper {top_match['flickr_id']} --missing --force")

            # Add other matches to 'Potential Duplicates' set
            for other_match in sorted_matches[1:]:
                commands.append(f'python add-set.py --set-name "Potential Duplicates" --id {other_match["flickr_id"]}')

    return commands

def main():
    audit_results = load_audit_results()

    all_commands = []

    # Process timestamp matches
    timestamp_commands = process_matches(audit_results['timestamp_matches'], 'timestamp')
    all_commands.extend(timestamp_commands)

    # Process filename matches (assuming they're in the audit results)
    if 'filename_matches' in audit_results:
        filename_commands = process_matches(audit_results['filename_matches'], 'filename')
        all_commands.extend(filename_commands)

    # Write commands to log file
    with open('fix_commands.log', 'w') as f:
        for command in all_commands:
            f.write(f"{command}\n")

    print(f"Generated {len(all_commands)} commands. See fix_commands.log for details.")

if __name__ == "__main__":
    main()