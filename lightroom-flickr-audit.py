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
from audit_utils import load_secrets, perform_audit, print_audit_results
from flickr_ops import add_to_managed_set, authenticate_flickr, get_flickr_photos
from lightroom_ops import connect_to_lightroom_db, extract_xmp_document_id, get_flickr_sets, get_lr_photos

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

    flickr_photos = get_flickr_photos(flickr)  # Note: This gets all photos, not just for the set
    title_quote_count = sum(1 for photo in flickr_photos if '"' in photo['title'])
    print(f"Photos in Flickr containing double-quote in title (breaks lightroom plugin): {title_quote_count}")

    conn.close()

if __name__ == "__main__":
    main()