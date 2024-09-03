"""
merge.py: One-at-a-time fix for duplicate Flickr uploads caused by a broken Lightroom plugin.

This script addresses the issue of duplicate Flickr images caused by a broken Lightroom plugin.
It performs the following actions:
1. Takes two photo IDs (you can get a photo's ID by looking at the Flickr URL), --keeper and --goner. The --keeper photo is the one that will be kept, and the --goner photo will be deleted from Flickr.
2. Checks that both photo IDs exist in Flickr, and that the --goner photo is in the Lightroom catalog's AgRemotePhoto table.
3. Moves the --goner photo to a set named "To Be Deleted" in Flickr (for safety, actual deletion is left to the end-user)
4. Updates the Lightroom catalog entry to point the plugin published photo to the --keeper photo instead of the --goner photo.
5. Removes the --goner photo from the managed set if present.
6. Adds the --keeper photo to the managed set if not already present.

Usage:
  python merge.py --keeper [id] --goner [id] [--force] [--missing]

Requirements:
  - flickrapi library
  - secrets.json file with Flickr API credentials
  - SQLite3 (usually comes pre-installed with Python)

Note: Always backup your Lightroom catalog and EXIT LIGHTROOM before running this code.
"""

import json
import datetime
import re
import flickrapi
import argparse
import sqlite3

# Load secrets
with open('secrets.json') as f:
    secrets = json.load(f)

api_key = secrets['api_key']
api_secret = secrets['api_secret']
lightroom_db = secrets['lrcat_file_path']

def iso(epoch):
    return datetime.datetime.fromtimestamp(int(epoch)).isoformat()

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

def check_photo_exists(flickr, photo_id):
    """Check if a photo exists on Flickr and print its information if found."""
    try:
        photo_info = flickr.photos.getInfo(photo_id=photo_id, format='parsed-json')

        print(f"\nFlickr information for photo_id: {photo_id}")

        # Print basic information
        print(f"\tTitle: {photo_info['photo']['title']['_content']}")
        print(f"\tOwner: {photo_info['photo']['owner']['username']}")
        print(f"\tDate taken: {photo_info['photo']['dates']['taken']}")
        print(f"\tDate posted: {iso(photo_info['photo']['dates']['posted'])}")

        # Print tags
        print("\tTags:")
        for tag in photo_info['photo']['tags']['tag']:
            print(f"\t  - {tag['raw']}")

        # Print URLs
        print("\tURLs:")
        for size in photo_info['photo']['urls']['url']:
            print(f"\t  {size['type']}: {size['_content']}")

        # Print permissions
        print("\tPermissions:")
        print(f"\t  Public: {photo_info['photo']['visibility']['ispublic']}")
        print(f"\t  Friend: {photo_info['photo']['visibility']['isfriend']}")
        print(f"\t  Family: {photo_info['photo']['visibility']['isfamily']}")

        return True
    except flickrapi.exceptions.FlickrError as e:
        print(f"\nError: Photo with ID {photo_id} not found or not accessible.")
        print(f"Flickr API Error: {str(e)}")
        return False

def check_photo_in_lightroom(photo_id):
    """Check if a photo exists in the Lightroom AgRemotePhoto table and print column names and values."""
    conn = sqlite3.connect(lightroom_db)
    cursor = conn.cursor()

    # Get column names
    cursor.execute("PRAGMA table_info(AgRemotePhoto)")
    columns = [column[1] for column in cursor.fetchall()]

    # Check if photo exists and get its values
    cursor.execute("SELECT * FROM AgRemotePhoto WHERE remoteId = ?", (photo_id,))
    row = cursor.fetchone()

    if row:
        print("\nLightroom info for photo with remoteId =", photo_id)
        for column, value in zip(columns, row):
            print(f"\t{column}: {value}")
        exists = True
    else:
        print(f"\nNo photo found with remoteId = {photo_id}")
        exists = False

    conn.close()
    return exists

def get_managed_set_id(photo_id):
    """Derive the managed set ID from the URL in the AgRemotePhoto table for a specific photo."""
    conn = sqlite3.connect(lightroom_db)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT url FROM AgRemotePhoto WHERE remoteId = ?", (photo_id,))
        result = cursor.fetchone()
        if result and result[0]:
            url = result[0]
            # Extract set ID from URL
            match = re.search(r'https://www\.flickr\.com/photos/[^/]+/\d+/in/set-(\d+)', url)
            if match:
                return match.group(1)
            else:
                print(f"Warning: Could not extract set ID from URL for photo {photo_id}")
                return None
        else:
            print(f"Warning: No URL found for photo {photo_id} in AgRemotePhoto table.")
            return None
    except sqlite3.Error as e:
        print(f"Error querying the database: {e}")
        return None
    finally:
        conn.close()

def move_to_delete_set(flickr, photo_id):
    """Move a photo to the 'To Be Deleted' set."""
    # Check if 'To Be Deleted' set exists, create if not
    sets = flickr.photosets.getList(format='parsed-json')
    delete_set_id = None
    for photoset in sets['photosets']['photoset']:
        if photoset['title']['_content'] == 'To Be Deleted':
            delete_set_id = photoset['id']
            break

    if not delete_set_id:
        try:
            # Create the set with the goner photo
            new_set = flickr.photosets.create(title='To Be Deleted', primary_photo_id=photo_id, format='parsed-json')
            delete_set_id = new_set['photoset']['id']
            print(f"Created 'To Be Deleted' set with ID: {delete_set_id}")
        except flickrapi.exceptions.FlickrError as e:
            print(f"Error creating 'To Be Deleted' set: {str(e)}")
            return
    else:
        try:
            # Add the photo to the existing set
            flickr.photosets.addPhoto(photoset_id=delete_set_id, photo_id=photo_id, format='parsed-json')
            print(f"Added photo {photo_id} to existing 'To Be Deleted' set")
        except flickrapi.exceptions.FlickrError as e:
            print(f"Note: {str(e)}")
            return

    print(f"Successfully moved photo {photo_id} to 'To Be Deleted' set")

def update_lightroom_catalog(goner_id, keeper_id):
    """Update the Lightroom catalog to point to the keeper photo."""
    conn = sqlite3.connect(lightroom_db)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE AgRemotePhoto
        SET remoteId = ?, url = REPLACE(url, ?, ?), photoNeedsUpdating = 1.0,
                   serviceAggregateRating = 2.0
        WHERE remoteId = ?
    """, (keeper_id, goner_id, keeper_id, goner_id))
    conn.commit()
    conn.close()
    print(f"Updated Lightroom catalog: remapped {goner_id} to {keeper_id}")

def remove_from_managed_set(flickr, photo_id, lr_managed_set_id):
    """Remove the goner photo from the managed set."""
    try:
        flickr.photosets.removePhoto(photoset_id=lr_managed_set_id, photo_id=photo_id, format='parsed-json')
        print(f"Removed photo {photo_id} from managed set {lr_managed_set_id}")
    except flickrapi.exceptions.FlickrError as e:
        print(f"Error removing photo {photo_id} from managed set: {str(e)}")

def add_to_managed_set(flickr, photo_id, lr_managed_set_id):
    """Add the keeper photo to the managed set if not already present."""
    try:
        # Check if the photo is already in the set
        photos_in_set = flickr.photosets.getPhotos(photoset_id=lr_managed_set_id, format='parsed-json')
        if any(photo['id'] == photo_id for photo in photos_in_set['photoset']['photo']):
            print(f"Photo {photo_id} is already in the managed set {lr_managed_set_id}")
        else:
            flickr.photosets.addPhoto(photoset_id=lr_managed_set_id, photo_id=photo_id, format='parsed-json')
            print(f"Added photo {photo_id} to managed set {lr_managed_set_id}")
    except flickrapi.exceptions.FlickrError as e:
        print(f"Error adding photo {photo_id} to managed set: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Fix duplicate Flickr uploads caused by a broken Lightroom plugin.")
    parser.add_argument("--keeper", required=True, help="ID of the photo to keep")
    parser.add_argument("--goner", required=True, help="ID of the photo to be deleted")
    parser.add_argument("--force", action="store_true", help="Actually perform changes (default is dry-run)")
    parser.add_argument("--missing", action="store_true", help="Indicate that the goner photo is already gone")
    args = parser.parse_args()

    dry_run = not args.force

    if dry_run:
        print("Running in dry-run mode. Use --force to actually make changes.")
    else:
        print("Running in FORCE mode. Changes will be applied!")

    # Initialize Flickr API with authentication
    flickr = authenticate()

    # Get the managed set ID from the AgRemotePhoto table for the goner photo
    lr_managed_set_id = get_managed_set_id(args.goner)
    if lr_managed_set_id:
        print(f"Managed set ID derived from AgRemotePhoto table for photo {args.goner}: {lr_managed_set_id}")
    else:
        print(f"Error: Could not derive managed set ID for photo {args.goner}. Exiting.")
        return

    # Check if keeper photo exists on Flickr
    if not check_photo_exists(flickr, args.keeper):
        print(f"Error: Keeper photo {args.keeper} does not exist on Flickr.")
        return

    # Check if goner photo exists on Flickr (skip if --missing is set)
    if not args.missing:
        if not check_photo_exists(flickr, args.goner):
            print(f"Error: Goner photo {args.goner} does not exist on Flickr.")
            return
    else:
        print(f"Skipping Flickr check for goner photo {args.goner} as it is marked as missing.")

    # Check if goner photo is in Lightroom catalog
    if not check_photo_in_lightroom(args.goner):
        print(f"Error: Goner photo {args.goner} is not in the Lightroom catalog.")
        return

    # Move goner photo to 'To Be Deleted' set (skip if --missing is set)
    if not args.missing:
        if not dry_run:
            move_to_delete_set(flickr, args.goner)
        else:
            print(f"[DRY RUN] Would move photo {args.goner} to 'To Be Deleted' set")

        # Remove goner from managed set
        if not dry_run:
            remove_from_managed_set(flickr, args.goner, lr_managed_set_id)
        else:
            print(f"[DRY RUN] Would remove photo {args.goner} from managed set {lr_managed_set_id}")
    else:
        print(f"Skipping moving goner photo {args.goner} to 'To Be Deleted' set and removing it from managed set as it is marked as missing.")

    # Add keeper to managed set
    if not dry_run:
        add_to_managed_set(flickr, args.keeper, lr_managed_set_id)
    else:
        print(f"[DRY RUN] Would add photo {args.keeper} to managed set {lr_managed_set_id}")

    # Update Lightroom catalog
    if not dry_run:
        update_lightroom_catalog(args.goner, args.keeper)
    else:
        print(f"[DRY RUN] Would update Lightroom catalog: remap {args.goner} to {args.keeper}")

    print("Operation completed successfully.")

if __name__ == "__main__":
    main()
