"""
swap.py: Swap Flickr photo references for two photos in the Lightroom catalog.

This script addresses the need to swap Flickr photo references for two photos in the Lightroom catalog.
It performs the following actions:
1. Takes two Flickr photo IDs (remoteId) as input arguments
2. Retrieves the corresponding id_local values from the Lightroom catalog.
3. Swaps the Flickr IDs (remoteId) and URLs for the two photos in the Lightroom catalog.
4. Assumes both photos are already in the managed set on Flickr.

Usage:
  python swap.py [Flickr_photo_id1] [Flickr_photo_id2] [--force]

Requirements:
  - flickrapi library
  - secrets.json file with Flickr API credentials
  - SQLite3 (usually comes pre-installed with Python)

Note: Always backup your Lightroom catalog and EXIT LIGHTROOM before running this code.
"""

import json
import flickrapi
import argparse
import sqlite3

# Load secrets
with open('secrets.json') as f:
    secrets = json.load(f)

api_key = secrets['api_key']
api_secret = secrets['api_secret']
lightroom_db = secrets['lrcat_file_path']

def authenticate():
    """Authenticate with Flickr and get OAuth token."""
    flickr = flickrapi.FlickrAPI(api_key, api_secret)

    if not flickr.token_valid(perms='write'):
        flickr.get_request_token(oauth_callback='oob')
        authorize_url = flickr.auth_url(perms='write')
        print(f"Please open this URL: {authorize_url}")
        verifier = input('Enter the verification code: ')
        flickr.get_access_token(verifier)

    return flickr

def get_photo_info(remote_id):
    """Get id_local and url for a photo from the Lightroom catalog using remoteId."""
    conn = sqlite3.connect(lightroom_db)
    cursor = conn.cursor()

    cursor.execute("SELECT id_local, url FROM AgRemotePhoto WHERE remoteId = ?", (remote_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result
    else:
        print(f"\nNo photo found with remoteId = {remote_id}")
        return None

def swap_photos_in_lightroom(id_local1, remote_id1, url1, id_local2, remote_id2, url2):
    """Swap the Flickr photo references for two photos in the Lightroom catalog."""
    conn = sqlite3.connect(lightroom_db)
    cursor = conn.cursor()

    try:
        # Start a transaction
        cursor.execute("BEGIN TRANSACTION")

        # First, set one remoteId to 0 to avoid UNIQUE constraint violation
        cursor.execute("""
            UPDATE AgRemotePhoto
            SET remoteId = 0
            WHERE id_local = ?
        """, (id_local1,))

        # Update the second photo
        cursor.execute("""
            UPDATE AgRemotePhoto
            SET remoteId = ?, url = ?, photoNeedsUpdating = 1.0
            WHERE id_local = ?
        """, (remote_id1, url1, id_local2))

        # Update the first photo
        cursor.execute("""
            UPDATE AgRemotePhoto
            SET remoteId = ?, url = ?, photoNeedsUpdating = 1.0
            WHERE id_local = ?
        """, (remote_id2, url2, id_local1))

        # Commit the transaction
        conn.commit()
        print(f"Swapped Flickr photo references for photos {remote_id1} and {remote_id2} in Lightroom catalog.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Swap Flickr photo references for two photos in the Lightroom catalog.")
    parser.add_argument("photo1", help="Flickr ID of the first photo")
    parser.add_argument("photo2", help="Flickr ID of the second photo")
    parser.add_argument("--force", action="store_true", help="Actually perform changes (default is dry-run)")
    args = parser.parse_args()

    dry_run = not args.force

    if dry_run:
        print("Running in dry-run mode. Use --force to actually make changes.")
    else:
        print("Running in FORCE mode. Changes will be applied!")

    # Initialize Flickr API with authentication
    authenticate()

    # Get photo info for both photos
    photo1_info = get_photo_info(args.photo1)
    photo2_info = get_photo_info(args.photo2)

    if not photo1_info or not photo2_info:
        print("Error: One or both photos not found in the Lightroom catalog.")
        return

    id_local1, url1 = photo1_info
    id_local2, url2 = photo2_info

    print(f"\nCurrent state:")
    print(f"Photo1 (remoteId: {args.photo1}) -> id_local: {id_local1}")
    print(f"Photo2 (remoteId: {args.photo2}) -> id_local: {id_local2}")

    # Swap remoteId and url
    if not dry_run:
        swap_photos_in_lightroom(id_local1, args.photo1, url1, id_local2, args.photo2, url2)
    else:
        print(f"\n[DRY RUN] Would swap Flickr photo references:")
        print(f"Photo with id_local {id_local1}: {args.photo1} -> {args.photo2}")
        print(f"Photo with id_local {id_local2}: {args.photo2} -> {args.photo1}")

    print("\nOperation completed successfully.")
    print("Note: Both photos are assumed to be already in the managed set on Flickr.")

if __name__ == "__main__":
    main()