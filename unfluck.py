# unfluck.py:
# throwaway script to revert a mass of duplicate uploads from Lightroom Flickr plugin
import json
import sys
import flickrapi
import argparse
import webbrowser
import sqlite3
from datetime import datetime
from collections import defaultdict

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
        webbrowser.open_new_tab(authorize_url)
        verifier = input('Enter verification code: ')
        flickr.get_access_token(verifier)

    return flickr

# Initialize Flickr API with authentication
flickr = authenticate()

def move_to_delete_set(photo_id, dry_run=True):
    """Move a photo to the 'To Be Deleted' set."""
    if dry_run:
        print(f"[DRY RUN] Would move photo {photo_id} to 'To Be Deleted' set")
        return

    # Check if 'To Be Deleted' set exists, create if not
    sets = flickr.photosets.getList(format='parsed-json')
    delete_set_id = next((photoset['id'] for photoset in sets['photosets']['photoset']
                          if photoset['title']['_content'] == 'To Be Deleted'), None)

    if not delete_set_id:
        # Create the set with the photo to be deleted
        new_set = flickr.photosets.create(title='To Be Deleted', primary_photo_id=photo_id, format='parsed-json')
        delete_set_id = new_set['photoset']['id']
        print(f"Created 'To Be Deleted' set with ID: {delete_set_id}")
    else:
        # Add the photo to the existing set
        flickr.photosets.addPhoto(photoset_id=delete_set_id, photo_id=photo_id, format='parsed-json')

    print(f"Moved photo {photo_id} to 'To Be Deleted' set")

def update_lightroom_database(unwanted_id, golden_id, dry_run=True):
    """Update Lightroom database to remap photo IDs."""
    if dry_run:
        print(f"[DRY RUN] Would update Lightroom database: remap {unwanted_id} to {golden_id}")
        return

    conn = sqlite3.connect(lightroom_db)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE AgRemotePhoto
        SET remoteId = ?, url = REPLACE(url, ?, ?), photoNeedsUpdating = 1
        WHERE remoteId = ?
    """, (golden_id, unwanted_id, golden_id, unwanted_id))
    conn.commit()
    conn.close()

    print(f"Updated Lightroom database: remapped {unwanted_id} to {golden_id}")

def remove_from_managed_set(photo_id, dry_run=True):
    """Remove the photo from the managed set."""
    if dry_run:
        print(f"[DRY RUN] Would remove photo {photo_id} from managed set {set_id}")
        return

    flickr.photosets.removePhoto(photoset_id=set_id, photo_id=photo_id, format='parsed-json')
    print(f"Removed photo {photo_id} from managed set {set_id}")

def add_to_managed_set(photo_id, dry_run=True):
    """Add the photo to the managed set if not already present."""
    if dry_run:
        print(f"[DRY RUN] Would add photo {photo_id} to managed set {set_id}")
        return

    # Check if the photo is already in the set
    photos_in_set = flickr.photosets.getPhotos(photoset_id=set_id, format='parsed-json')
    if any(photo['id'] == photo_id for photo in photos_in_set['photoset']['photo']):
        print(f"Photo {photo_id} is already in the managed set {set_id}")
    else:
        flickr.photosets.addPhoto(photoset_id=set_id, photo_id=photo_id, format='parsed-json')
        print(f"Added photo {photo_id} to managed set {set_id}")

def process_lightroom_photos(start_date, all_photos, dry_run=True, process_multi_match=False, max_views=100):
    """Process photos in the Lightroom database against ls-all.jsonl."""
    conn = sqlite3.connect(lightroom_db)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT remoteId
        FROM AgRemotePhoto
        WHERE url LIKE 'https://www.flickr.com/%'
    """)

    lr_photos = [i for (i,) in cursor.fetchall()]
    conn.close()

    # Create a dictionary for quick lookup of photo details
    photo_details = {photo['photo_id']: photo for photo in all_photos}

    multiple_matches = defaultdict(lambda: {'lr_photos': [], 'matching_photos': []})

    for lr_photo_id in lr_photos:
        if lr_photo_id not in photo_details:
            continue

        lr_photo = photo_details[lr_photo_id]
        date_uploaded = lr_photo['date_upload']
        date_uploaded_dt = datetime.strptime(date_uploaded, "%Y-%m-%dT%H:%M:%S")
        date_taken = lr_photo['date_taken']

        # Check if the photo was uploaded after the start date
        if date_uploaded_dt < start_date:
            continue

        # Check if the photo has enough views
        views = lr_photo['views']
        if views > max_views:
            # print(f"Skipping photo {lr_photo_id} with {views} views (above threshold of {max_views})")
            continue

        # Find matching photos in all_photos
        matching_photos = [p for p in all_photos
                           if p['date_taken'] == date_taken
                            and p['photo_id'] != lr_photo_id
                            and p['photo_id'] not in lr_photos]
        match_count = len(matching_photos)

        if match_count == 1:
            print(f"Processing photo {lr_photo_id} uploaded on {date_uploaded}, title={lr_photo['title']}")
            matching_photo = matching_photos[0]
            # Move the Lightroom photo to 'To Be Deleted' set
            move_to_delete_set(lr_photo_id, dry_run)

            # Update Lightroom database
            update_lightroom_database(lr_photo_id, matching_photo['photo_id'], dry_run)

            # Remove the deleted photo from the managed set
            remove_from_managed_set(lr_photo_id, dry_run)

            # Add the keeper photo to the managed set
            add_to_managed_set(matching_photo['photo_id'], dry_run)

            print(f"{'[DRY RUN] Would remap' if dry_run else 'Remapped'} {lr_photo_id} to {matching_photo['photo_id']}")
        elif match_count > 1 and process_multi_match:
            raise "too complicated, not supported yet"
        elif match_count > 1:
            # If multi-match processing is not enabled, just log the multiple matches
            multiple_matches[date_taken]['lr_photos'].append(lr_photo_id)
            multiple_matches[date_taken]['matching_photos'].extend([p['photo_id'] for p in matching_photos])

    # Print details for photos with multiple matches
    if multiple_matches:
        print("\nPhotos with multiple matches:")
        for date_taken, matches in multiple_matches.items():
            print(f"  Date taken: {date_taken}")
            print(f"    Lightroom photo IDs: {', '.join(matches['lr_photos'])}")
            print(f"    Matching photo IDs (from ls-all.jsonl): {', '.join(matches['matching_photos'])}")

def main():
    parser = argparse.ArgumentParser(description="Process Lightroom photos against ls-all.jsonl and update Lightroom database.")
    parser.add_argument("start_date", help="Start date for processing (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help="Actually perform changes (default is dry-run)")
    parser.add_argument("--multi-match", action="store_true", help="Process photos with multiple matches")
    parser.add_argument("--max-views", type=int, default=100, help="Skip photos with fewer views than this (default: 100)")
    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    dry_run = not args.force

    if dry_run:
        print("Running in dry-run mode. Use --force to actually make changes.")
    else:
        print("Running in FORCE mode. Changes will be applied!")

    if args.multi_match:
        print("Multi-match processing is enabled.")
    else:
        print("Multi-match processing is disabled. Use --multi-match to enable.")

    print(f"Skipping photos with fewer than {args.max_views} views.")

    # Load all photos from ls-all.jsonl
    with open('ls-all.jsonl', 'r') as f:
        all_photos = [json.loads(line) for line in f]

    # Process Lightroom photos
    process_lightroom_photos(start_date, all_photos, dry_run, args.multi_match, args.max_views)

    print("\nOperation completed successfully.")

if __name__ == "__main__":
    main()