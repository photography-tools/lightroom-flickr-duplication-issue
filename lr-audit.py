# lr-audit.py:
#  Audit and fix Lightroom-Flickr set mismatches.
#  This script will check for photos in the Lightroom catalog that are missing from Flickr, or are in Flickr but missing from the LR-managed Set.
#  It will then add the missing photos to the managed Flickr set.
#  This script requires a secrets.json file with the following
#  keys: api_key, api_secret, set_id, lrcat_file_path
#  You can obtain the API key and secret from Flickr's developer portal.
#  The set_id is the ID of the Flickr set you want to manage.
#  The lrcat_file_path is the path to your Lightroom catalog file.
#  This script uses the flickrapi library to interact with Flickr.
#  You can install it with pip install flickrapi.

import json
import flickrapi
import argparse
import sqlite3

# Load secrets
with open('secrets.json') as f:
    secrets = json.load(f)

api_key = secrets['api_key']
api_secret = secrets['api_secret']
managed_set_id = secrets['set_id']
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

def get_lr_remote_ids():
    """Get all Flickr remote IDs from the Lightroom database."""
    conn = sqlite3.connect(lightroom_db)
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT remoteId
        FROM AgRemotePhoto
        WHERE url LIKE 'https://www.flickr.com/%' and url LIKE '%/in/set-{managed_set_id}'
    """)

    lr_remote_ids = set(i for (i,) in cursor.fetchall())
    conn.close()

    return lr_remote_ids

def get_photos_in_managed_set(flickr):
    """Get all photos in the managed Flickr set."""
    photos = set()
    page = 1
    per_page = 500

    while True:
        response = flickr.photosets.getPhotos(
            photoset_id=managed_set_id,
            page=page,
            per_page=per_page,
            format='parsed-json'
        )
        photos.update(photo['id'] for photo in response['photoset']['photo'])
        print(f"Fetched page {page} of managed set photos")

        if page >= response['photoset']['pages']:
            break

        page += 1

    return photos

def check_photo_exists(flickr, photo_id):
    """Check if a photo exists on Flickr."""
    try:
        flickr.photos.getInfo(photo_id=photo_id)
        return True
    except flickrapi.exceptions.FlickrError:
        return False

def add_to_managed_set(flickr, photo_id):
    """Add a photo to the managed set."""
    try:
        flickr.photosets.addPhoto(photoset_id=managed_set_id, photo_id=photo_id)
        print(f"Added photo {photo_id} to managed set")
    except flickrapi.exceptions.FlickrError as e:
        print(f"Error adding photo {photo_id} to managed set: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Audit and fix Lightroom-Flickr set mismatches.")
    parser.add_argument("--force", action="store_true", help="Execute the fix (default is dry-run)")
    args = parser.parse_args()

    dry_run = not args.force

    if dry_run:
        print("Running in dry-run mode. Use --force to actually make changes.")
    else:
        print("Running in FORCE mode. Changes will be applied!")

    # Initialize Flickr API with authentication
    flickr = authenticate()

    # Get remote IDs from Lightroom
    lr_remote_ids = get_lr_remote_ids()
    print(f"Found {len(lr_remote_ids)} remote IDs in Lightroom database")

    # Get photos in managed set
    managed_set_photos = get_photos_in_managed_set(flickr)
    print(f"Found {len(managed_set_photos)} photos in managed Flickr set")

    # Process mismatches
    missing_from_flickr = 0
    not_in_managed_set = 0

    print("\nProcessing mismatches:")
    for photo_id in lr_remote_ids:
        if photo_id not in managed_set_photos:
            if check_photo_exists(flickr, photo_id):
                print(f"Photo {photo_id} exists on Flickr but not in managed set")
                not_in_managed_set += 1
                if not dry_run:
                    add_to_managed_set(flickr, photo_id)
            else:
                print(f"Photo {photo_id} is missing from Flickr")
                missing_from_flickr += 1

    print("\nAudit completed.")
    print(f"{missing_from_flickr} photos are missing from Flickr. You may need to re-upload these or update your Lightroom catalog.")
    if dry_run:
        print(f"{not_in_managed_set} photos would be added to the managed set. Run with --force to apply changes.")
    else:
        print(f"{not_in_managed_set} photos were added to the managed set.")

if __name__ == "__main__":
    main()