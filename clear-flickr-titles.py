import json
import os
import sqlite3
from datetime import datetime
import flickrapi
import argparse
from flickr_ops import get_flickr_photos

def load_secrets():
    with open('secrets.json') as f:
        return json.load(f)

def authenticate_flickr(api_key, api_secret):
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
    if not flickr.token_valid(perms='write'):
        flickr.get_request_token(oauth_callback='oob')
        authorize_url = flickr.auth_url(perms='write')
        print(f"Please authorize this app: {authorize_url}")
        verifier = input('Verifier code: ')
        flickr.get_access_token(verifier)
    return flickr

def get_lr_published_photos(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT remoteId, url
        FROM AgRemotePhoto
        WHERE url LIKE '%flickr.com%' AND url LIKE '%/in/set-%'
    """)
    photos = cursor.fetchall()
    conn.close()
    return {photo[0]: photo[1] for photo in photos}

def clear_photo_title(flickr, photo_id, new_title):
    flickr.photos.setMeta(photo_id=photo_id, title=new_title)

def main():
    parser = argparse.ArgumentParser(description='Clear Flickr photo titles in Lightroom published sets and set them to photo IDs.')
    parser.add_argument('--force', action='store_true', help='Actually perform changes (default is dry-run)')
    args = parser.parse_args()

    dry_run = not args.force

    if dry_run:
        print("Running in dry-run mode. Use --force to actually make changes.")
    else:
        print("WARNING: Running in FORCE mode. Changes will be applied!")
        confirm = input("Are you sure you want to proceed? (y/n): ").lower().strip()
        if confirm != 'y':
            print("Operation cancelled.")
            return

    secrets = load_secrets()
    flickr = authenticate_flickr(secrets['api_key'], secrets['api_secret'])

    log_data = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"title_change_log_{timestamp}.json"

    lr_photos = get_lr_published_photos(secrets['lrcat_file_path'])
    print(f"Found {len(lr_photos)} photos in Lightroom published sets")

    all_flickr_photos = get_flickr_photos(flickr)
    print(f"Retrieved {len(all_flickr_photos)} photos from Flickr")

    total_photos = 0
    changed_photos = 0

    for photo in all_flickr_photos:
        photo_id = photo['id']
        if photo_id in lr_photos:
            total_photos += 1
            old_title = photo['title']
            new_title = photo_id

            if old_title != new_title:
                if not dry_run:
                    clear_photo_title(flickr, photo_id, new_title)
                    print(f"Changed title for photo {photo_id}: '{old_title}' -> '{new_title}'")
                else:
                    print(f"[DRY RUN] Would change title for photo {photo_id}: '{old_title}' -> '{new_title}'")

                log_data[photo_id] = {
                    "old_title": old_title,
                    "new_title": new_title,
                    "lr_url": lr_photos[photo_id]
                }
                changed_photos += 1
            else:
                print(f"Skipped photo {photo_id}: Title already matches photo ID")

    with open(log_filename, 'w') as log_file:
        json.dump(log_data, log_file, indent=2)

    print(f"\nProcessed {total_photos} photos from Lightroom published sets.")
    print(f"{'Changed' if not dry_run else 'Would change'} titles for {changed_photos} photos.")
    print(f"Log file saved as: {log_filename}")

if __name__ == "__main__":
    main()