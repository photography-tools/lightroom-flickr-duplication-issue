"""
lightroom_flickr_audit_main.py: Main script for Lightroom-Flickr Audit

This script integrates the flickr_operations and lightroom_operations modules
to perform a comprehensive audit between Lightroom catalogs and Flickr sets.

Usage:
    python lightroom_flickr_audit_main.py [--fix] [--deep] [--brief]

Options:
    --fix     Execute fixes for mismatches (default is dry-run)
    --deep    Perform a deep audit, including XMP metadata analysis
    --brief   Output concise results focusing on key identification fields

Requirements:
    - Python 3.6+
    - flickrapi library
    - lxml library (for XML parsing)
    - secrets.json file with necessary credentials and paths
"""

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime

# Import functions from our modules
from flickr_ops import add_to_managed_set, authenticate_flickr, get_flickr_photos
from lightroom_ops import connect_to_lightroom_db, get_flickr_sets, get_lr_photos

def load_secrets():
    """Load secrets from the secrets.json file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    secrets_path = os.path.join(script_dir, 'secrets.json')

    try:
        with open(secrets_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: secrets.json file not found at {secrets_path}")
        print("Please create a secrets.json file with your Flickr API credentials and Lightroom catalog path.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in secrets.json file at {secrets_path}")
        print("Please ensure the file contains valid JSON.")
        exit(1)

def extract_xmp_document_id(xmp_data):
    """Extract XMP Document ID from XMP data."""
    if xmp_data and isinstance(xmp_data, dict):
        rdf = xmp_data.get('x:xmpmeta', {}).get('rdf:RDF', {})
        description = rdf.get('rdf:Description', {})
        return description.get('@xmpMM:DocumentID')
    return None

def normalize_timestamp(timestamp_str):
    """Convert various timestamp formats to epoch seconds."""
    # Try parsing as ISO format (from Flickr)
    try:
        return int(datetime.fromisoformat(timestamp_str).timestamp())
    except ValueError:
        pass

    # Try parsing as Unix timestamp (from Lightroom)
    try:
        return int(float(timestamp_str))
    except ValueError:
        pass

    # If all else fails, return None
    return None

def perform_audit(lr_photos, flickr_photos, deep_scan):
    """Perform audit between Lightroom and Flickr photos."""
    flickr_dict_by_id = {photo['id']: photo for photo in flickr_photos}
    flickr_dict_by_timestamp = defaultdict(list)
    flickr_dict_by_filename = defaultdict(list)
    flickr_dict_by_document_id = defaultdict(list)

    for photo in flickr_photos:
        epoch_time = normalize_timestamp(photo['datetaken'])
        if epoch_time:
            flickr_dict_by_timestamp[epoch_time].append(photo)
        flickr_dict_by_filename[photo['title'].lower()].append(photo)

        # Add document ID processing for deep scan
        if deep_scan:
            doc_id = photo.get('xmp_document_id')  # Assume this is extracted elsewhere
            if doc_id:
                flickr_dict_by_document_id[doc_id].append(photo)

    audit_results = {
        "in_lr_not_in_flickr": [],
        "timestamp_matches": [],
        "filename_matches": [],
        "document_id_matches": [],
        "no_matches": []
    }

    for lr_photo in lr_photos:
        if lr_photo["lr_remote_id"] in flickr_dict_by_id:
            continue

        lr_timestamp = normalize_timestamp(lr_photo['adobe_images'].get('captureTime'))
        lr_filename = lr_photo['ag_library_file'].get('baseName', '').lower()

        if lr_timestamp and lr_timestamp in flickr_dict_by_timestamp:
            audit_results["timestamp_matches"].append({
                "lr_photo": lr_photo,
                "flickr_matches": flickr_dict_by_timestamp[lr_timestamp]
            })
        elif lr_filename in flickr_dict_by_filename:
            audit_results["filename_matches"].append({
                "lr_photo": lr_photo,
                "flickr_matches": flickr_dict_by_filename[lr_filename]
            })
        elif deep_scan:
            xmp_did = extract_xmp_document_id(lr_photo['adobe_additional_metadata'].get('xmp'))
            if xmp_did and xmp_did in flickr_dict_by_document_id:
                audit_results["document_id_matches"].append({
                    "lr_photo": lr_photo,
                    "flickr_matches": flickr_dict_by_document_id[xmp_did]
                })
            else:
                audit_results["no_matches"].append(lr_photo)
        else:
            audit_results["no_matches"].append(lr_photo)

    return audit_results

def get_brief_photo_info(photo, is_lr=True):
    """Extract brief identification information from a photo."""
    if is_lr:
        return {
            "lr_id": photo.get("lr_id"),
            "lr_global_id": photo.get("lr_global_id"),
            "lr_remote_id": photo.get("lr_remote_id"),
            "filename": photo['ag_library_file'].get('baseName', ''),
            "capture_time": photo['adobe_images'].get('captureTime')
        }
    else:
        return {
            "flickr_id": photo.get("id"),
            "title": photo.get("title"),
            "date_taken": photo.get("datetaken")
        }

def print_audit_results(audit_results, brief=False):
    """Print audit results to stdout."""
    for category in ["timestamp_matches", "filename_matches", "document_id_matches", "no_matches"]:
        print(f"\n{category.replace('_', ' ').title()}:")
        for item in audit_results[category]:
            if isinstance(item, dict) and "lr_photo" in item:
                lr_info = get_brief_photo_info(item["lr_photo"])
                print("\nLightroom Photo:")
                if "flickr_matches" in item:
                    lr_info['flickr_matches'] = []
                    for match in item["flickr_matches"]:
                        flickr_info = get_brief_photo_info(match, is_lr=False)
                        lr_info['flickr_matches'].append(flickr_info)
                print(json.dumps(lr_info, indent=2))
            else:
                lr_info = get_brief_photo_info(item)
                print("\nLightroom Photo (No matches):")
                print(json.dumps(lr_info, indent=2))

def main():
    parser = argparse.ArgumentParser(description='Lightroom-Flickr Audit and Synchronization Utility')
    parser.add_argument('--fix', action='store_true', help='Execute fixes for mismatches (default is dry-run)')
    parser.add_argument('--brief', action='store_true', help='Output concise results focusing on key identification fields')
    parser.add_argument('--no-deep', action='store_true', help='Disable deep scan (XMP metadata analysis)')
    args = parser.parse_args()

    secrets = load_secrets()
    flickr = authenticate_flickr(secrets['api_key'], secrets['api_secret'])

    conn = connect_to_lightroom_db(secrets['lrcat_file_path'])

    flickr_sets = get_flickr_sets(conn)
    print(f"Detected {len(flickr_sets)} Flickr sets in Lightroom catalog")

    for set_id in flickr_sets:
        print(f"\nProcessing Flickr set: {set_id}")
        lr_photos = get_lr_photos(conn, set_id)
        flickr_photos = get_flickr_photos(flickr)  # Note: This gets all photos, not just for the set

        audit_results = perform_audit(lr_photos, flickr_photos, not args.no_deep)

        # Logical progression report
        total_lr_photos = len(lr_photos)
        total_flickr_photos = len(flickr_photos)
        in_lr_not_in_flickr = len(audit_results["in_lr_not_in_flickr"])
        timestamp_matches = len(audit_results["timestamp_matches"])
        filename_matches = len(audit_results["filename_matches"])
        document_id_matches = len(audit_results["document_id_matches"])
        no_matches = len(audit_results["no_matches"])

        print(f"\nAudit Results for set {set_id}:")
        print(f"Total photos in Lightroom set: {total_lr_photos}")
        print(f"Total photos in Flickr account: {total_flickr_photos}")
        print(f"Photos in Lightroom publish set but not in Flickr: {in_lr_not_in_flickr}")
        print(f"  - Timestamp matches: {timestamp_matches}")
        print(f"  - Filename matches: {filename_matches}")
        if not args.no_deep:
            print(f"  - XMP Document ID matches: {document_id_matches}")
        print(f"  - No matches found: {no_matches}")

        print_audit_results(audit_results, args.brief)

        if args.fix:
            print(f"\nExecuting fixes for set {set_id}:")
            for photo in audit_results["no_matches"]:
                if photo["lr_remote_id"]:
                    add_to_managed_set(flickr, photo["lr_remote_id"], set_id)
        else:
            print("\nDry run completed. Use --fix to apply changes.")

    conn.close()

if __name__ == "__main__":
    main()