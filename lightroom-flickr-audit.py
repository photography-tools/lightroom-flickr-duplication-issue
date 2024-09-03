"""
lightroom_flickr_audit_main.py: Main script for Lightroom-Flickr Audit

This script integrates the flickr_operations and lightroom_operations modules
to perform a comprehensive audit between Lightroom catalogs and Flickr sets.

Usage:
    python lightroom_flickr_audit_main.py [--fix-singles] [--fix-sets] [--prune] [--brief] [--no-deep] [--debug]

Options:
    --fix-singles Repoint Lightroom to single Flickr match for single matches only
    --fix-sets    Add photos to their expected Flickr sets
    --prune       Identify and optionally delete low-engagement Flickr matches (views < 100, comments == 0, favorites == 0)
    --brief       Output concise results focusing on key identification fields
    --no-deep     Disable deep scan (XMP metadata analysis)
    --debug       Enable debug output
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

# Import functions from our modules
from audit_utils import load_secrets, perform_audit, print_audit_results
from flickr_ops import add_to_managed_set, authenticate_flickr, get_all_photos_in_set, get_flickr_photos, delete_flickr_photo
from lightroom_ops import connect_to_lightroom_db, extract_xmp_document_id, get_flickr_sets, get_lr_photos, update_lr_remote_id

def print_flush(message):
    """Print a message and flush the output."""
    print(message, flush=True)

def identify_low_engagement_matches(flickr, audit_results, verbose=False):
    to_be_pruned = defaultdict(list)
    total_photos = sum(len(audit_results[k]) for k in ["timestamp_matches", "filename_matches", "document_id_matches"])
    processed = 0

    for match_type in ["timestamp_matches", "filename_matches", "document_id_matches"]:
        for photo in audit_results[match_type]:
            processed += 1
            if processed % 100 == 0:
                print_flush(f"Processed {processed}/{total_photos} photos")

            if len(photo["flickr_matches"]) >= 2:
                low_engagement_matches = []
                highest_views = -1
                highest_views_id = None
                for match in photo["flickr_matches"]:
                    try:
                        views = int(match['views'])
                        if views < 100:
                            comments = int(match['count_comments'])
                            favorites = len(flickr.photos.getFavorites(photo_id=match["id"])['photo']['person'])

                            print_flush(f"{match['id']} v={views} c={comments} f={favorites}")

                            if comments == 0 and favorites == 0:
                                low_engagement_matches.append(match["id"])

                        if views > highest_views:
                            highest_views = views
                            highest_views_id = match["id"]

                    except Exception as e:
                        if verbose:
                            print_flush(f"Error getting info for photo {match['id']}: {str(e)}")

                if len(low_engagement_matches) < len(photo["flickr_matches"]):
                    to_be_pruned[photo["lr_photo"]["lr_remote_id"]] = low_engagement_matches
                else:
                    to_be_pruned[photo["lr_photo"]["lr_remote_id"]] = [id for id in low_engagement_matches if id != highest_views_id]
                    print_flush(f"All matches for photo {photo['lr_photo']['lr_remote_id']} are low engagement. Keeping photo {highest_views_id} with {highest_views} views.")

    return to_be_pruned

def prune_low_engagement_matches(flickr, to_be_pruned, debug=False):
    pruned_photos = defaultdict(list)
    for lr_remote_id, flickr_ids in to_be_pruned.items():
        for flickr_id in flickr_ids:
            if debug:
                print_flush(f"Attempting to delete Flickr photo {flickr_id}")
            try:
                delete_flickr_photo(flickr, flickr_id)
                pruned_photos[lr_remote_id].append(flickr_id)
            except Exception as e:
                print_flush(f"Failed to delete Flickr photo {flickr_id}: {str(e)}")
    return pruned_photos

def add_photos_to_set(flickr, photos_to_add, set_id, debug=False):
    added_photos = []
    for photo_id in photos_to_add:
        if debug:
            print_flush(f"Attempting to add photo {photo_id} to set {set_id}")
        try:
            add_to_managed_set(flickr, photo_id, set_id)
            added_photos.append(photo_id)
        except Exception as e:
            print_flush(f"Failed to add photo {photo_id} to set {set_id}: {str(e)}")
    return added_photos

def main():
    parser = argparse.ArgumentParser(description='Lightroom-Flickr Audit and Synchronization Utility')
    parser.add_argument('--fix-singles', action='store_true', help='Repoint Lightroom to single Flickr match for single matches only')
    parser.add_argument('--fix-sets', action='store_true', help='Add photos to their expected Flickr sets')
    parser.add_argument('--prune', action='store_true', help='Identify and optionally delete low-engagement Flickr matches')
    parser.add_argument('--brief', action='store_true', help='Output concise results focusing on key identification fields')
    parser.add_argument('--no-deep', action='store_true', help='Disable deep scan (XMP metadata analysis)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    if args.debug:
        print_flush("Debug mode enabled")

    secrets = load_secrets()
    flickr = authenticate_flickr(secrets['api_key'], secrets['api_secret'])

    conn = connect_to_lightroom_db(secrets['lrcat_file_path'])

    lightroom_flickr_sets = get_flickr_sets(conn)
    print_flush(f"Detected {len(lightroom_flickr_sets)} Flickr sets in Lightroom catalog")

    all_flickr_photos = get_flickr_photos(flickr)
    print_flush(f"Retrieved {len(all_flickr_photos)} photos from Flickr account")

    all_to_be_pruned = defaultdict(dict)
    all_to_be_added = defaultdict(list)

    for set_id in lightroom_flickr_sets:
        print_flush(f"\nProcessing Flickr set: {set_id}")
        lr_photos = get_lr_photos(conn, set_id)
        if args.debug:
            print_flush(f"Retrieved {len(lr_photos)} photos from Lightroom for set {set_id}")

        flickr_photos = get_flickr_photos(flickr)
        if args.debug:
            print_flush(f"Retrieved {len(flickr_photos)} photos from Flickr")

        audit_results = perform_audit(lr_photos, flickr_photos, not args.no_deep)

        flickr_photos_in_set = get_all_photos_in_set(flickr, set_id)
        flickr_photos_in_set_ids = {photo['id'] for photo in flickr_photos_in_set}

        in_lr_not_in_set = [
            lr_photo for lr_photo in lr_photos
            if lr_photo['lr_remote_id'] not in flickr_photos_in_set_ids
        ]

        total_lr_photos = len(lr_photos)
        total_flickr_photos = len(flickr_photos)
        total_flickr_photos_in_set = len(flickr_photos_in_set)
        in_lr_not_in_flickr = len(audit_results["in_lr_not_in_flickr"])
        in_lr_not_in_set_count = len(in_lr_not_in_set)
        timestamp_matches = len(audit_results["timestamp_matches"])
        filename_matches = len(audit_results["filename_matches"])
        document_id_matches = len(audit_results["document_id_matches"])
        no_matches = len(audit_results["no_matches"])

        print_flush(f"\nAudit Results for set {set_id}:")
        print_flush(f"Total photos in Lightroom set: {total_lr_photos}")
        print_flush(f"Total photos in Flickr account: {total_flickr_photos}")
        print_flush(f"Total photos in Flickr set: {total_flickr_photos_in_set}")
        print_flush(f"Photos in Lightroom publish set but not in Flickr: {in_lr_not_in_flickr}")
        print_flush(f"Photos in Lightroom but not in expected Flickr set: {in_lr_not_in_set_count}")
        print_flush(f"  - Timestamp matches: {timestamp_matches}")
        print_flush(f"  - Filename matches: {filename_matches}")
        if not args.no_deep:
            print_flush(f"  - XMP Document ID matches: {document_id_matches}")
        print_flush(f"  - No matches found: {no_matches}")

        print_audit_results(audit_results, args.brief)

        if args.prune:
            if args.debug:
                print_flush(f"Identifying low engagement matches for set {set_id}")
            to_be_pruned = identify_low_engagement_matches(flickr, audit_results, args.debug)
            all_to_be_pruned[set_id] = to_be_pruned

        if args.fix_singles:
            print_flush(f"\nExecuting basic fixes for set {set_id}:")
            for match_type in ["timestamp_matches", "filename_matches", "document_id_matches"]:
                for photo in audit_results[match_type]:
                    if len(photo["flickr_matches"]) == 1:
                        flickr_id = photo["flickr_matches"][0]["id"]
                        old_flickr_id = photo["lr_photo"]["lr_remote_id"]
                        update_lr_remote_id(conn, old_flickr_id, flickr_id)
        else:
            print_flush("\nDry run completed. Use --fix-singles to apply changes.")

        if args.fix_sets:
            photos_to_add = [photo['lr_remote_id'] for photo in in_lr_not_in_set]
            all_to_be_added[set_id].extend(photos_to_add)

    if args.prune:
        print_flush("\nLow engagement Flickr matches identified for deletion:")
        total_to_delete = sum(len(photos) for set_data in all_to_be_pruned.values() for photos in set_data.values())
        print_flush(f"Total photos to be deleted: {total_to_delete}")
        for set_id, to_be_pruned in all_to_be_pruned.items():
            print_flush(f"\nSet {set_id}:")
            for lr_remote_id, flickr_ids in to_be_pruned.items():
                print_flush(f"  Lightroom remote ID: {lr_remote_id}")
                print_flush(f"    Flickr IDs to delete: {', '.join(flickr_ids)}")

        confirm = input("\nDo you want to proceed with deletion? (y/n): ").lower().strip()
        if confirm == 'y':
            if os.path.isfile('ls-all.json'):
                os.unlink('ls-all.json')  # invalidate local cache
            all_pruned_photos = defaultdict(dict)
            for set_id, to_be_pruned in all_to_be_pruned.items():
                if args.debug:
                    print_flush(f"Pruning low engagement matches for set {set_id}")
                pruned_photos = prune_low_engagement_matches(flickr, to_be_pruned, args.debug)
                all_pruned_photos[set_id] = pruned_photos

            print_flush("\nPruning completed. Deleted photos:")
            for set_id, pruned_photos in all_pruned_photos.items():
                print_flush(f"\nSet {set_id}:")
                for lr_remote_id, flickr_ids in pruned_photos.items():
                    print_flush(f"  Lightroom remote ID: {lr_remote_id}")
                    print_flush(f"    Deleted Flickr IDs: {', '.join(flickr_ids)}")
        else:
            print_flush("Pruning cancelled. No photos were deleted.")

    if args.fix_sets:
        print_flush("\nPhotos to be added to their expected Flickr sets:")
        total_to_add = sum(len(photos) for photos in all_to_be_added.values())
        print_flush(f"Total photos to be added: {total_to_add}")
        for set_id, photos in all_to_be_added.items():
            print_flush(f"\nSet {set_id}:")
            print_flush(f"  Photos to add: {', '.join(photos)}")

        confirm = input("\nDo you want to proceed with adding photos to sets? (y/n): ").lower().strip()
        if confirm == 'y':
            all_added_photos = defaultdict(list)
            for set_id, photos_to_add in all_to_be_added.items():
                if args.debug:
                    print_flush(f"Adding photos to set {set_id}")
                added_photos = add_photos_to_set(flickr, photos_to_add, set_id, args.debug)
                all_added_photos[set_id] = added_photos

            print_flush("\nAdding photos to sets completed:")
            for set_id, added_photos in all_added_photos.items():
                print_flush(f"\nSet {set_id}:")
                print_flush(f"  Added photos: {', '.join(added_photos)}")
        else:
            print_flush("Adding photos to sets cancelled. No changes were made.")

    flickr_photos = get_flickr_photos(flickr)  # Note: This gets all photos, not just for the set
    title_quote_count = sum(1 for photo in flickr_photos if '"' in photo['title'])
    print_flush(f"\nPhotos in Flickr containing double-quote in title (breaks lightroom plugin): {title_quote_count}")

    conn.close()

if __name__ == "__main__":
    main()
