"""
lr_flickr_audit.py: Main script for Lightroom-Flickr managed set synchronization audit

This script coordinates the audit process between Lightroom catalog and Flickr set,
utilizing separate modules for Lightroom and Flickr operations.

Usage:
    python lr_flickr_audit.py [--full]

Options:
    --full    Scan the entire Lightroom catalog, not just the publish set

Requirements:
    - Python 3.6+
    - flickrapi library
    - lxml library (for XML parsing)
    - secrets.json file with necessary credentials and paths
"""

import argparse
import json
from collections import defaultdict
import os
import sys
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from lightroom_operations import get_lr_photos, connect_to_lightroom_db, get_all_lr_photos
from flickr_operations import authenticate_flickr, get_flickr_photos, find_filename_matches

def load_secrets():
    with open('secrets.json') as f:
        return json.load(f)

def get_lr_timestamp(lr_photo):
    # Extract timestamp from adobe_images data
    capture_time = lr_photo['adobe_images'].get('captureTime')
    if capture_time:
        try:
            # Assuming the format is 'YYYY-MM-DD HH:MM:SS'
            dt = datetime.strptime(capture_time, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return capture_time
    return None

def get_lr_filename(lr_photo):
    # Extract filename from ag_library_file data
    return lr_photo['ag_library_file'].get('baseName')

def main():
    parser = argparse.ArgumentParser(description='Deep audit utility for Lightroom-Flickr managed set synchronization')
    parser.add_argument('--full', action='store_true', help='Scan the entire Lightroom catalog')
    args = parser.parse_args()

    secrets = load_secrets()
    flickr = authenticate_flickr(secrets['api_key'], secrets['api_secret'])

    conn = connect_to_lightroom_db(secrets['lrcat_file_path'])
    
    if args.full:
        print("Scanning the entire Lightroom catalog...")
        lr_photos = get_all_lr_photos(conn)
    else:
        print(f"Scanning Lightroom publish set (ID: {secrets['set_id']})...")
        lr_photos = get_lr_photos(conn, secrets['set_id'])
    
    conn.close()

    flickr_photos = get_flickr_photos(flickr)

    flickr_dict_by_id = {photo['id']: photo for photo in flickr_photos}
    flickr_dict_by_timestamp = defaultdict(list)
    for photo in flickr_photos:
        flickr_dict_by_timestamp[photo['datetaken']].append(photo)

    audit_results = {
        "id_matches": [],
        "timestamp_matches": [],
        "filename_matches": [],
        "missing_from_flickr": [],
        "in_lightroom_not_in_flickr": []
    }

    for lr_photo in lr_photos:
        # Check for ID match first
        if lr_photo["lr_remote_id"] in flickr_dict_by_id:
            audit_results["id_matches"].append({
                **lr_photo,
                "flickr_match": flickr_dict_by_id[lr_photo["lr_remote_id"]]
            })
        else:
            # If no ID match, check for timestamp match
            lr_timestamp = get_lr_timestamp(lr_photo)
            if lr_timestamp and lr_timestamp in flickr_dict_by_timestamp:
                audit_results["timestamp_matches"].append({
                    **lr_photo,
                    "flickr_matches": flickr_dict_by_timestamp[lr_timestamp]
                })
            else:
                # If no ID or timestamp match, check for filename match
                lr_filename = get_lr_filename(lr_photo)
                if lr_filename:
                    filename_matches = find_filename_matches(lr_filename, flickr_photos)
                    if filename_matches:
                        audit_results["filename_matches"].append({
                            **lr_photo,
                            "flickr_matches": filename_matches
                        })
                    else:
                        audit_results["missing_from_flickr"].append(lr_photo)
                else:
                    audit_results["missing_from_flickr"].append(lr_photo)

    # Find photos in Lightroom but not in Flickr
    lr_remote_ids = set(photo["lr_remote_id"] for photo in lr_photos if photo["lr_remote_id"])
    flickr_ids = set(photo["id"] for photo in flickr_photos)
    in_lr_not_in_flickr = lr_remote_ids - flickr_ids
    audit_results["in_lightroom_not_in_flickr"] = [
        photo for photo in lr_photos if photo["lr_remote_id"] in in_lr_not_in_flickr
    ]

    # Summary counters
    total_lr_photos = len(lr_photos)
    total_flickr_photos = len(flickr_photos)
    id_matches = len(audit_results["id_matches"])
    timestamp_matches = len(audit_results["timestamp_matches"])
    filename_matches = len(audit_results["filename_matches"])
    missing_from_flickr = len(audit_results["missing_from_flickr"])
    in_lr_not_in_flickr = len(audit_results["in_lightroom_not_in_flickr"])

    print("\nAudit Results:")
    print(f"Total photos in Lightroom {'catalog' if args.full else 'publish set'}: {total_lr_photos}")
    print(f"Total photos in Flickr set: {total_flickr_photos}")
    print(f"Photos with ID matches: {id_matches}")
    print(f"Photos with timestamp matches (no ID match): {timestamp_matches}")
    print(f"Photos with filename matches (no ID or timestamp match): {filename_matches}")
    print(f"Photos missing from Flickr: {missing_from_flickr}")
    print(f"Photos in Lightroom but not in Flickr: {in_lr_not_in_flickr}")

    output_filename = 'lr_flickr_audit_results_full.json' if args.full else 'lr_flickr_audit_results.json'
    with open(output_filename, 'w') as f:
        json.dump(audit_results, f, indent=2, default=str)

    print(f"\nDetailed results saved to {output_filename}")

if __name__ == "__main__":
    main()
