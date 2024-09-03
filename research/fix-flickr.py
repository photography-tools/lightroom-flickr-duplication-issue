# fix-flickr.py
# Description: Script to process Flickr photos based on audit results from audit.py

import json
import sys
import flickrapi
import argparse
import webbrowser
from datetime import datetime

# Load secrets
with open('secrets.json') as f:
    secrets = json.load(f)

api_key = secrets['api_key']
api_secret = secrets['api_secret']
set_id = secrets['set_id']

def authenticate():
    """Authenticate with Flickr and get OAuth token."""
    flickr = flickrapi.FlickrAPI(api_key, api_secret)

    if not flickr.token_valid(perms='delete'):
        flickr.get_request_token(oauth_callback='oob')
        authorize_url = flickr.auth_url(perms='delete')
        webbrowser.open_new_tab(authorize_url)
        verifier = input('Enter verification code: ')
        flickr.get_access_token(verifier)

    return flickr

# Initialize Flickr API with authentication
flickr = authenticate()

def remove_from_set(photo_id, dry_run=True):
    """Remove a photo from the specified set."""
    if dry_run:
        print(f"[DRY RUN] Would remove photo {photo_id} from set {set_id}")
    else:
        try:
            flickr.photosets.removePhoto(photoset_id=set_id, photo_id=photo_id)
            print(f"Removed photo {photo_id} from set {set_id}")
        except Exception as e:
            print(f"Error removing photo {photo_id} from set: {str(e)}")

def delete_photo(photo_id, reason, dry_run=True):
    """Delete a photo from Flickr."""
    if dry_run:
        print(f"[DRY RUN] Would delete photo {photo_id} ({reason})")
    else:
        try:
            flickr.photos.delete(photo_id=photo_id)
            print(f"Deleted photo {photo_id} ({reason})")
        except Exception as e:
            print(f"Error deleting photo {photo_id} ({reason}): {str(e)}")

def is_correctly_missing(photo):
    """Check if a photo is 'correctly missing in Lightroom'."""
    upload_date = datetime.fromisoformat(photo['date_upload'].rstrip('Z'))
    return upload_date >= datetime(2024, 8, 24) and photo["matching"]

def has_favorites_or_comments(photo):
    """Check if a photo has favorites or comments."""
    return int(photo.get('favorites', 0)) > 0 or int(photo.get('comments', 0)) > 0

def process_photo(photo, dry_run=True):
    """
    Process a single photo missing from Lightroom.

    :param photo: The photo to process
    :param dry_run: Whether to actually perform actions
    """
    if is_correctly_missing(photo):
        if not has_favorites_or_comments(photo):
            delete_photo(photo["photo_id"], "correctly missing in Lightroom", dry_run)
        else:
            print(f"{'[DRY RUN] Would skip deletion' if dry_run else 'Skipped deletion'} of photo {photo['photo_id']} due to favorites or comments")
            remove_from_set(photo["photo_id"], dry_run)
    elif photo["matching"]:
        # There's a matching (newer) image
        matching_photo = photo["matching"][0]
        if not has_favorites_or_comments(matching_photo):
            delete_photo(matching_photo["photo_id"], f"golden image: {photo['photo_id']}", dry_run)
        else:
            print(f"{'[DRY RUN] Would skip deletion' if dry_run else 'Skipped deletion'} of matching photo {matching_photo['photo_id']} due to favorites or comments")
            remove_from_set(photo["photo_id"], dry_run)
    else:
        # No matching image, remove from set
        remove_from_set(photo["photo_id"], dry_run)

def process_flickr_updates(audit_results, dry_run=True):
    """Process the missing photos from the audit results and perform Flickr updates."""
    missing_in_lightroom = audit_results["missing_in_lightroom"]

    for photo in missing_in_lightroom:
        process_photo(photo, dry_run)

def main():
    parser = argparse.ArgumentParser(description="Process Flickr photos based on audit results.")
    parser.add_argument("audit_file", help="Path to the audit results JSON file")
    parser.add_argument("--force", action="store_true", help="Actually perform changes (default is dry-run)")
    args = parser.parse_args()

    # Load audit results
    with open(args.audit_file, 'r') as f:
        audit_results = json.load(f)

    # Process the missing photos and perform Flickr updates
    dry_run = not args.force
    if dry_run:
        print("Running in dry-run mode. Use --force to actually make changes.")
    else:
        print("Running in FORCE mode. Changes will be applied!")

    process_flickr_updates(audit_results, dry_run)

if __name__ == "__main__":
    main()

"""
Example usage:

1. Dry-run mode (default):
   python fix-flickr.py audit_results.json

2. Force mode (actually make changes):
   python fix-flickr.py audit_results.json --force

Example output in dry-run mode:

Running in dry-run mode. Use --force to actually make changes.
[DRY RUN] Would delete photo 53949265761 (correctly missing in Lightroom)
[DRY RUN] Would skip deletion of photo 53949265762 due to favorites or comments
[DRY RUN] Would remove photo 53949265762 from set 12345
[DRY RUN] Would remove photo 53949265763 from set 12345
[DRY RUN] Would delete photo 53949265764 (golden image: 14097127336)

Example output in force mode:

Running in FORCE mode. Changes will be applied!
Deleted photo 53949265761 (correctly missing in Lightroom)
Skipped deletion of photo 53949265762 due to favorites or comments
Removed photo 53949265762 from set 12345
Removed photo 53949265763 from set 12345
Deleted photo 53949265764 (golden image: 14097127336)
"""