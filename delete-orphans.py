# delete-orphans.py:
# Deletes orphaned photos that exist in the Lightroom publish collection but not in the managed Flickr set.
# Has some additional options for skipping photos with high view counts.


import json
import flickrapi
import argparse
import sqlite3
from datetime import datetime

# Load secrets
with open('secrets.json') as f:
    secrets = json.load(f)

api_key = secrets['api_key']
api_secret = secrets['api_secret']
set_id = secrets['set_id']
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

def get_photos_in_managed_set(flickr):
    """Get all photos in the managed Flickr set."""
    photos = []
    page = 1
    per_page = 500

    while True:
        response = flickr.photosets.getPhotos(
            photoset_id=set_id,
            page=page,
            per_page=per_page,
            extras='views',
            format='parsed-json'
        )
        photos.extend(response['photoset']['photo'])

        if page >= response['photoset']['pages']:
            break

        page += 1

    return photos

def get_photos_in_lightroom():
    """Get all Flickr photo IDs from the Lightroom database."""
    conn = sqlite3.connect(lightroom_db)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT remoteId
        FROM AgRemotePhoto
        WHERE url LIKE 'https://www.flickr.com/%'
    """)

    lr_photos = set(i for (i,) in cursor.fetchall())
    conn.close()

    return lr_photos

def get_or_create_to_be_deleted_set(flickr):
    """Get or create the 'To Be Deleted' set."""
    sets = flickr.photosets.getList(format='parsed-json')
    for photoset in sets['photosets']['photoset']:
        if photoset['title']['_content'] == 'To Be Deleted':
            return photoset['id']

    # If the set doesn't exist, create it
    user = flickr.people.getInfo(format='parsed-json')
    first_photo = flickr.people.getPhotos(user_id=user['person']['id'], per_page=1, format='parsed-json')
    new_set = flickr.photosets.create(title='To Be Deleted', primary_photo_id=first_photo['photos']['photo'][0]['id'], format='parsed-json')
    return new_set['photoset']['id']

def move_photo_to_delete_set(flickr, photo_id, delete_set_id, dry_run=True):
    """Move a photo to the 'To Be Deleted' set."""
    if dry_run:
        print(f"[DRY RUN] Would move photo {photo_id} to 'To Be Deleted' set")
    else:
        try:
            flickr.photosets.addPhoto(photoset_id=delete_set_id, photo_id=photo_id)
            flickr.photosets.removePhoto(photoset_id=set_id, photo_id=photo_id)
            print(f"Moved photo {photo_id} to 'To Be Deleted' set")
        except flickrapi.exceptions.FlickrError as e:
            print(f"Error moving photo {photo_id}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Move orphaned photos from Flickr to 'To Be Deleted' set.")
    parser.add_argument("--force", action="store_true", help="Actually perform moves (default is dry-run)")
    parser.add_argument("--max-views", type=int, default=100, help="Maximum number of views for moving (default: 100)")
    args = parser.parse_args()

    dry_run = not args.force
    max_views = args.max_views

    if dry_run:
        print("Running in dry-run mode. Use --force to actually move photos.")
    else:
        print("Running in FORCE mode. Photos will be moved!")

    print(f"Photos with more than {max_views} views will not be moved.")

    # Initialize Flickr API with authentication
    flickr = authenticate()

    # Get or create the 'To Be Deleted' set
    delete_set_id = get_or_create_to_be_deleted_set(flickr)
    print(f"'To Be Deleted' set ID: {delete_set_id}")

    # Get photos from the managed Flickr set
    flickr_photos = get_photos_in_managed_set(flickr)
    print(f"Found {len(flickr_photos)} photos in the managed Flickr set.")

    # Get photos from Lightroom database
    lr_photos = get_photos_in_lightroom()
    print(f"Found {len(lr_photos)} Flickr photos in the Lightroom database.")

    # Find orphaned photos
    orphaned_photos = [photo for photo in flickr_photos if photo['id'] not in lr_photos]
    print(f"Found {len(orphaned_photos)} orphaned photos.")

    # Process orphaned photos
    photos_to_move = 0
    photos_skipped = 0

    for photo in orphaned_photos:
        photo_id = photo['id']
        title = photo['title']
        views = int(photo['views'])

        print(f"Orphaned photo: {photo_id} - '{title}' - {views} views")

        if views > max_views:
            print(f"  Skipping move due to high view count ({views} > {max_views})")
            photos_skipped += 1
        else:
            move_photo_to_delete_set(flickr, photo_id, delete_set_id, dry_run)
            photos_to_move += 1

    print(f"\nOperation completed successfully.")
    print(f"Photos to be moved: {photos_to_move}")
    print(f"Photos skipped due to high view count: {photos_skipped}")

if __name__ == "__main__":
    main()