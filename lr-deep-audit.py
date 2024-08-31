"""
lr-deep-audit.py: Timestamp-normalized Deep audit utility for Lightroom-Flickr managed set synchronization

This script audits photos in a Lightroom catalog against a specific Flickr set,
extracting precise capture times from XMP metadata and normalizing timestamps for accurate matching.

Usage:
    python lr-deep-audit.py

Requirements:
    - Python 3.6+
    - flickrapi library
    - lxml library (for XML parsing)
    - secrets.json file with:
        {
            "api_key": "your_flickr_api_key",
            "api_secret": "your_flickr_api_secret",
            "lrcat_file_path": "/path/to/your/lightroom_catalog.lrcat",
            "set_id": "your_flickr_set_id"
        }

Output:
    - Console: Summary of audit results
    - lr_deep_audit_results.json: Detailed audit information for timestamp matches and missing photos

Audit results include:
    - Precise timestamp matches without ID matches
    - Photos missing from Flickr
"""

import argparse
import json
import os
import sqlite3
from datetime import datetime
import flickrapi
from collections import defaultdict
import zlib
from lxml import etree
import re
import struct

def load_secrets():
    with open('secrets.json') as f:
        return json.load(f)

def connect_to_lightroom_db(db_path):
    return sqlite3.connect(db_path)

def decompress_xmp(compressed_data):
    if len(compressed_data) < 4:
        return None

    uncompressed_length = struct.unpack('>I', compressed_data[:4])[0]

    try:
        decompressed_data = zlib.decompress(compressed_data[4:])
    except zlib.error:
        print("Failed to decompress XMP data")
        return None

    if len(decompressed_data) != uncompressed_length:
        print(f"Decompressed length ({len(decompressed_data)}) does not match expected length ({uncompressed_length})")

    return decompressed_data

def extract_capture_time_from_xmp(xmp_data):
    try:
        decompressed_xmp = decompress_xmp(xmp_data)
        if not decompressed_xmp:
            return None

        root = etree.fromstring(decompressed_xmp)

        nsmap = {
            'x': 'adobe:ns:meta/',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'xmp': 'http://ns.adobe.com/xap/1.0/',
            'exif': 'http://ns.adobe.com/exif/1.0/'
        }

        for path in [
            './/exif:DateTimeOriginal',
            './/xmp:CreateDate',
            './/exif:DateTimeDigitized'
        ]:
            element = root.find(path, namespaces=nsmap)
            if element is not None:
                return normalize_timestamp(element.text)

        date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
        match = date_pattern.search(decompressed_xmp.decode('utf-8', errors='ignore'))
        if match:
            return normalize_timestamp(match.group(0))

        return None
    except Exception as e:
        print(f"Error parsing XMP data: {e}")
        return None

def normalize_timestamp(timestamp):
    # Remove any timezone information and replace 'T' with space
    timestamp = re.sub(r'[+-]\d{2}:\d{2}$', '', timestamp)
    return timestamp.replace('T', ' ').strip()

def get_lr_photos(conn, set_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            Adobe_images.id_local,
            AgLibraryFile.baseName,
            AgRemotePhoto.remoteId,
            Adobe_AdditionalMetadata.xmp
        FROM Adobe_images
        JOIN AgLibraryFile ON Adobe_images.rootFile = AgLibraryFile.id_local
        JOIN AgRemotePhoto ON Adobe_images.id_local = AgRemotePhoto.photo
        LEFT JOIN Adobe_AdditionalMetadata ON Adobe_images.id_local = Adobe_AdditionalMetadata.image
        WHERE AgRemotePhoto.url LIKE ? AND AgRemotePhoto.url LIKE ?
    """, (f'%flickr.com%', f'%/in/set-{set_id}%'))

    lr_photos = []
    for row in cursor.fetchall():
        lr_id, lr_filename, flickr_id, xmp_data = row
        if xmp_data:
            capture_time = extract_capture_time_from_xmp(xmp_data)
            if capture_time:
                lr_photos.append({
                    "lr_id": lr_id,
                    "lr_filename": lr_filename,
                    "lr_timestamp": capture_time,
                    "lr_remote_id": flickr_id  # This is the remoteId from Lightroom
                })
            else:
                print(f"Warning: Could not extract capture time for photo {lr_id}")
        else:
            print(f"Warning: No XMP data for photo {lr_id}")
    return lr_photos

def authenticate_flickr(api_key, api_secret):
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
    if not flickr.token_valid(perms='read'):
        flickr.get_request_token(oauth_callback='oob')
        authorize_url = flickr.auth_url(perms='read')
        print(f"Please authorize this app: {authorize_url}")
        verifier = input('Verifier code: ')
        flickr.get_access_token(verifier)
    return flickr

def get_flickr_photos(flickr):
    if os.path.exists('ls-all.jsonl'):
        print("Reading photo list from ls-all.jsonl...")
        photos = []
        with open('ls-all.jsonl', 'r') as f:
            for line in f:
                photo = json.loads(line)
                photos.append({
                    'id': photo['photo_id'],
                    'title': photo.get('title', ''),
                    'datetaken': photo['date_taken'],
                    'views': photo['views']
                })
        print(f"Read {len(photos)} photos from ls-all.jsonl")
        return photos

    print("Fetching photo list from Flickr...")
    photos = []
    page = 1
    while True:
        try:
            response = flickr.people.getPhotos(user_id='me', extras='date_taken,original_format', page=page, per_page=500)
            photos.extend(response['photos']['photo'])
            print(f"Fetched page {page} ({len(response['photos']['photo'])} photos)")
            if page >= response['photos']['pages']:
                break
            page += 1
        except flickrapi.exceptions.FlickrError as e:
            print(f"Error fetching photos from Flickr: {e}")
            break

    print(f"Flickr account contains {len(photos)} photos")
    return photos

def find_filename_matches(lr_filename, flickr_photos):
    matches = []
    for photo in flickr_photos:
        if lr_filename.lower() in photo['title'].lower():
            matches.append(photo)
    return matches

def extract_xmp_identifiers(xmp_data):
    try:
        decompressed_xmp = decompress_xmp(xmp_data)
        if not decompressed_xmp:
            return None, None

        root = etree.fromstring(decompressed_xmp)

        nsmap = {
            'x': 'adobe:ns:meta/',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'xmp': 'http://ns.adobe.com/xap/1.0/',
            'xmpMM': 'http://ns.adobe.com/xap/1.0/mm/'
        }

        iid = root.find('.//xmpMM:InstanceID', namespaces=nsmap)
        did = root.find('.//xmpMM:DocumentID', namespaces=nsmap)

        return (iid.text if iid is not None else None,
                did.text if did is not None else None)

    except Exception as e:
        print(f"Error parsing XMP data for identifiers: {e}")
        return None, None

def get_lr_photos(conn, set_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            Adobe_images.id_local,
            Adobe_images.id_global,
            AgLibraryFile.baseName,
            AgRemotePhoto.remoteId,
            Adobe_AdditionalMetadata.xmp
        FROM Adobe_images
        JOIN AgLibraryFile ON Adobe_images.rootFile = AgLibraryFile.id_local
        JOIN AgRemotePhoto ON Adobe_images.id_local = AgRemotePhoto.photo
        LEFT JOIN Adobe_AdditionalMetadata ON Adobe_images.id_local = Adobe_AdditionalMetadata.image
        WHERE AgRemotePhoto.url LIKE ? AND AgRemotePhoto.url LIKE ?
    """, (f'%flickr.com%', f'%/in/set-{set_id}%'))

    lr_photos = []
    for row in cursor.fetchall():
        lr_id, lr_global_id, lr_filename, flickr_id, xmp_data = row
        if xmp_data:
            capture_time = extract_capture_time_from_xmp(xmp_data)
            xmp_iid, xmp_did = extract_xmp_identifiers(xmp_data)
            if capture_time:
                lr_photos.append({
                    "lr_id": lr_id,
                    "lr_global_id": lr_global_id,
                    "lr_filename": lr_filename,
                    "lr_timestamp": capture_time,
                    "lr_remote_id": flickr_id,  # This is the remoteId from Lightroom
                    "xmp_iid": xmp_iid,
                    "xmp_did": xmp_did
                })
            else:
                print(f"Warning: Could not extract capture time for photo {lr_id}")
        else:
            print(f"Warning: No XMP data for photo {lr_id}")
    return lr_photos

def main():
    parser = argparse.ArgumentParser(description='Enhanced Deep audit utility for Lightroom-Flickr managed set synchronization')
    args = parser.parse_args()

    secrets = load_secrets()
    flickr = authenticate_flickr(secrets['api_key'], secrets['api_secret'])

    conn = connect_to_lightroom_db(secrets['lrcat_file_path'])
    lr_photos = get_lr_photos(conn, secrets['set_id'])
    conn.close()

    flickr_photos = get_flickr_photos(flickr)

    flickr_dict_by_id = {photo['id']: photo for photo in flickr_photos}
    flickr_dict_by_timestamp = defaultdict(list)
    for photo in flickr_photos:
        normalized_timestamp = normalize_timestamp(photo['datetaken'])
        flickr_dict_by_timestamp[normalized_timestamp].append(photo)

    audit_results = {
        "id_matches": [],
        "timestamp_matches": [],
        "filename_matches": [],
        "missing_from_flickr": []
    }

    for lr_photo in lr_photos:
        # Check for ID match first
        if lr_photo["lr_remote_id"] in flickr_dict_by_id:
            audit_results["id_matches"].append({
                "lr_id": lr_photo["lr_id"],
                "lr_global_id": lr_photo["lr_global_id"],
                "lr_filename": lr_photo["lr_filename"],
                "lr_timestamp": lr_photo["lr_timestamp"],
                "lr_remote_id": lr_photo["lr_remote_id"],
                "xmp_iid": lr_photo["xmp_iid"],
                "xmp_did": lr_photo["xmp_did"],
                "flickr_match": {
                    "flickr_id": flickr_dict_by_id[lr_photo["lr_remote_id"]]["id"],
                    "flickr_title": flickr_dict_by_id[lr_photo["lr_remote_id"]]["title"],
                    "flickr_date_taken": flickr_dict_by_id[lr_photo["lr_remote_id"]]["datetaken"],
                    "flickr_views": flickr_dict_by_id[lr_photo["lr_remote_id"]]["views"]
                }
            })
        # If no ID match, check for timestamp match
        elif lr_photo["lr_timestamp"] in flickr_dict_by_timestamp:
            audit_results["timestamp_matches"].append({
                "lr_id": lr_photo["lr_id"],
                "lr_global_id": lr_photo["lr_global_id"],
                "lr_filename": lr_photo["lr_filename"],
                "lr_timestamp": lr_photo["lr_timestamp"],
                "lr_remote_id": lr_photo["lr_remote_id"],
                "xmp_iid": lr_photo["xmp_iid"],
                "xmp_did": lr_photo["xmp_did"],
                "flickr_matches": [
                    {
                        "flickr_id": photo["id"],
                        "flickr_title": photo["title"],
                        "flickr_date_taken": photo["datetaken"],
                        "flickr_views": photo["views"]
                    }
                    for photo in flickr_dict_by_timestamp[lr_photo["lr_timestamp"]]
                ]
            })
        else:
            # If no ID or timestamp match, check for filename match
            filename_matches = find_filename_matches(lr_photo["lr_filename"], flickr_photos)
            if filename_matches:
                audit_results["filename_matches"].append({
                    "lr_id": lr_photo["lr_id"],
                    "lr_global_id": lr_photo["lr_global_id"],
                    "lr_filename": lr_photo["lr_filename"],
                    "lr_timestamp": lr_photo["lr_timestamp"],
                    "lr_remote_id": lr_photo["lr_remote_id"],
                    "xmp_iid": lr_photo["xmp_iid"],
                    "xmp_did": lr_photo["xmp_did"],
                    "flickr_matches": [
                        {
                            "flickr_id": photo["id"],
                            "flickr_title": photo["title"],
                            "flickr_date_taken": photo["datetaken"],
                            "flickr_views": photo["views"]
                        }
                        for photo in filename_matches
                    ]
                })
            else:
                audit_results["missing_from_flickr"].append({
                    "lr_id": lr_photo["lr_id"],
                    "lr_global_id": lr_photo["lr_global_id"],
                    "lr_filename": lr_photo["lr_filename"],
                    "lr_timestamp": lr_photo["lr_timestamp"],
                    "lr_remote_id": lr_photo["lr_remote_id"],
                    "xmp_iid": lr_photo["xmp_iid"],
                    "xmp_did": lr_photo["xmp_did"]
                })

    # Summary counters
    total_lr_photos = len(lr_photos)
    total_flickr_photos = len(flickr_photos)
    id_matches = len(audit_results["id_matches"])
    timestamp_matches = len(audit_results["timestamp_matches"])
    filename_matches = len(audit_results["filename_matches"])
    missing_from_flickr = len(audit_results["missing_from_flickr"])

    print("\nAudit Results:")
    print(f"Total photos in Lightroom set: {total_lr_photos}")
    print(f"Total photos in Flickr set: {total_flickr_photos}")
    print(f"Photos with ID matches: {id_matches}")
    print(f"Photos with timestamp matches (no ID match): {timestamp_matches}")
    print(f"Photos with filename matches (no ID or timestamp match): {filename_matches}")
    print(f"Photos missing from Flickr: {missing_from_flickr}")

    with open('lr_deep_audit_results.json', 'w') as f:
        json.dump(audit_results, f, indent=2)

    print("\nDetailed results saved to lr_deep_audit_results.json")

if __name__ == "__main__":
    main()