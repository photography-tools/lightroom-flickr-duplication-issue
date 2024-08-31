# audit.py
# Compares flickr set with lightroom publish collection dump.
# Usage: python audit.py <path_to_flickr_ls> <path_to_lightroom_dump>
# This is an early attempt at LR stuff, and works fine but has been
# superseded by other scripts that connect directly to the LR database
# and Flickr API.

import json
import sys
import codecs
from datetime import datetime

with open('secrets.json') as f:
    secrets = json.load(f)
    set_id = secrets['set_id']

def load_flickr_jsonl(file_path):
    """Load JSONL file and return a dictionary of photo_id to photo data."""
    photos = {}
    with codecs.open(file_path, 'r', encoding='utf-16') as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                photo_id = data['photo_id']
                photos[photo_id] = data
    return photos

def load_lightroom_dump(file_path):
    """Load the file with remoteId and return a dictionary of remoteId to photo data."""
    remote_photos = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            if item['url'].endswith(f'/in/set-{set_id}'):
                remote_id = item['remoteId']
                remote_photos[remote_id] = item
    return remote_photos

def find_matching_photos(target_photo, all_photos):
    """Find photos with the same date_taken as the target photo."""
    target_date = datetime.fromisoformat(target_photo['date_taken'])
    return [
        photo for photo_id, photo in all_photos.items()
        if photo_id != target_photo['photo_id'] and datetime.fromisoformat(photo['date_taken']) == target_date
    ]

def audit_photos(jsonl_path, remote_id_path):
    """Audit the photos by comparing photo_ids from JSONL with remoteIds."""
    jsonl_photos = load_flickr_jsonl(jsonl_path)
    remote_photos = load_lightroom_dump(remote_id_path)

    # Find mismatches
    missing_in_flickr = set(remote_photos.keys()) - set(jsonl_photos.keys())
    missing_in_lightroom = set(jsonl_photos.keys()) - set(remote_photos.keys())

    # Prepare results
    results = {
        "total_photos_in_flickr": len(jsonl_photos),
        "total_photos_in_lightroom": len(remote_photos),
        "missing_in_flickr_count": len(missing_in_flickr),
        "missing_in_lightroom_count": len(missing_in_lightroom),
        "missing_in_flickr": list(missing_in_flickr),
        "missing_in_lightroom": []
    }

    # Find matching photos for each missing in Lightroom
    for photo_id in missing_in_lightroom:
        photo = jsonl_photos[photo_id]
        matching_photos = find_matching_photos(photo, jsonl_photos)
        photo_with_matching = photo.copy()
        photo_with_matching['matching'] = matching_photos
        results["missing_in_lightroom"].append(photo_with_matching)

    # Output results as JSON
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python audit.py <path_to_flickr_ls> <path_to_lightroom_dump>")
        sys.exit(1)

    jsonl_path = sys.argv[1]
    remote_id_path = sys.argv[2]
    audit_photos(jsonl_path, remote_id_path)