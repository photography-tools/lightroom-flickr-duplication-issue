"""
lr-flickr-reconnect.py: Scan LR published set for photos missing from Flickr and suggest reconnections

This script scans the Lightroom catalog for photos in the Flickr published set that are missing from Flickr,
suggests potential matches based on exact timestamp, and interactively asks for confirmation before updating
the AgRemotePhoto accordingly.

Usage:
    python lr-flickr-reconnect.py <path_to_lightroom_catalog>

Arguments:
    path_to_lightroom_catalog: Path to the Lightroom catalog file (.lrcat)

Requirements:
    - Python 3.6+
    - flickrapi library
    - lxml library (for XML parsing)
    - secrets.json file with necessary credentials and paths
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime
import sqlite3
from lxml import etree
import flickrapi
from lightroom_ops import connect_to_lightroom_db, decompress_xmp, parse_xmp
from flickr_ops import authenticate_flickr, get_flickr_photos

def load_secrets():
    with open('secrets.json') as f:
        return json.load(f)

def get_flickr_set_id(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT url
        FROM AgRemotePhoto
        WHERE url LIKE '%flickr.com%' AND url LIKE '%/in/set-%'
        LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        match = re.search(r'/in/set-(\d+)', result[0])
        if match:
            return match.group(1)
    return None

def get_lr_photos_in_published_set(conn, set_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            Adobe_images.id_local,
            AgLibraryFile.baseName,
            AgLibraryFile.extension,
            AgLibraryFolder.pathFromRoot,
            AgRemotePhoto.remoteId,
            Adobe_AdditionalMetadata.xmp
        FROM Adobe_images
        JOIN AgLibraryFile ON Adobe_images.rootFile = AgLibraryFile.id_local
        JOIN AgLibraryFolder ON AgLibraryFile.folder = AgLibraryFolder.id_local
        JOIN AgLibraryPublishedCollectionImage ON Adobe_images.id_local = AgLibraryPublishedCollectionImage.image
        JOIN AgLibraryPublishedCollection ON AgLibraryPublishedCollectionImage.collection = AgLibraryPublishedCollection.id_local
        LEFT JOIN AgRemotePhoto ON Adobe_images.id_local = AgRemotePhoto.photo
        LEFT JOIN Adobe_AdditionalMetadata ON Adobe_images.id_local = Adobe_AdditionalMetadata.image
        WHERE AgLibraryPublishedCollection.remoteCollectionId = ?
    """, (set_id,))

    photos = []
    for row in cursor.fetchall():
        lr_id, base_name, extension, path_from_root, remote_id, xmp = row
        photo = {
            'lr_id': lr_id,
            'file_name': f"{base_name}.{extension}",
            'file_path': os.path.join(path_from_root, f"{base_name}.{extension}"),
            'remote_id': remote_id,
            'timestamp': None
        }

        if xmp:
            decompressed_xmp = decompress_xmp(xmp)
            if decompressed_xmp:
                xmp_data = parse_xmp(decompressed_xmp)
                if xmp_data:
                    photo['timestamp'] = xmp_data.get('xmp:CreateDate') or xmp_data.get('exif:DateTimeOriginal')

        photos.append(photo)

    return photos

def find_potential_flickr_match(photo, flickr_photos):
    if not photo['timestamp']:
        return None

    lr_timestamp = datetime.strptime(photo['timestamp'], "%Y-%m-%dT%H:%M:%S")
    potential_matches = []

    for flickr_photo in flickr_photos:
        flickr_timestamp = datetime.strptime(flickr_photo['datetaken'], "%Y-%m-%d %H:%M:%S")
        if lr_timestamp == flickr_timestamp:
            potential_matches.append(flickr_photo)

    return potential_matches[0] if potential_matches else None

def update_ag_remote_photo(conn, lr_id, flickr_id):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO AgRemotePhoto (photo, remoteId, serviceName)
        VALUES (?, ?, 'com.adobe.flickr')
    """, (lr_id, flickr_id))
    conn.commit()

def main(catalog_path):
    secrets = load_secrets()
    conn = connect_to_lightroom_db(catalog_path)
    flickr = authenticate_flickr(secrets['api_key'], secrets['api_secret'])

    set_id = get_flickr_set_id(conn)
    if not set_id:
        print("Error: Could not find Flickr published set in the Lightroom catalog.")
        conn.close()
        sys.exit(1)

    lr_photos = get_lr_photos_in_published_set(conn, set_id)
    flickr_photos = get_flickr_photos(flickr, set_id)

    missing_photos = [photo for photo in lr_photos if not photo['remote_id']]

    print(f"Found {len(missing_photos)} photos in the published set missing from Flickr.")

    for photo in missing_photos:
        potential_match = find_potential_flickr_match(photo, flickr_photos)

        if potential_match:
            print(f"\nPotential match found for {photo['file_name']}:")
            print(f"Lightroom timestamp: {photo['timestamp']}")
            print(f"Flickr photo: {potential_match['title']} (ID: {potential_match['id']})")
            print(f"Flickr timestamp: {potential_match['datetaken']}")

            user_input = input("Confirm match? (y/n): ").lower()

            if user_input == 'y':
                update_ag_remote_photo(conn, photo['lr_id'], potential_match['id'])
                print("Photo reconnected successfully.")
            else:
                print("Skipping this photo.")
        else:
            print(f"\nNo potential match found for {photo['file_name']}")

    conn.close()
    print("\nReconnection process completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconnect Lightroom photos with Flickr")
    parser.add_argument("catalog_path", help="Path to the Lightroom catalog file (.lrcat)")

    args = parser.parse_args()
    main(args.catalog_path)
