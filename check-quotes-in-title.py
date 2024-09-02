"""
check-quotes-in-title.py: Script to find titles with double quotes in Lightroom and Flickr

This script connects to a Lightroom catalog and Flickr, retrieves photos from the
publish collection, and identifies titles containing double quotes in both systems.

Usage:
    python check-quotes-in-title.py <path_to_lightroom_catalog>

Arguments:
    path_to_lightroom_catalog: Path to the Lightroom catalog file (.lrcat)

Output:
    Prints results to console and writes detailed results to a JSON file.
"""

import sqlite3
import sys
import json
from datetime import datetime
import flickrapi
import re
from lightroom_operations import connect_to_lightroom_db, decompress_xmp, parse_xmp
from flickr_operations import authenticate_flickr, get_flickr_photos

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

def get_lr_photos_with_quotes(conn):
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
        JOIN AgRemotePhoto ON Adobe_images.id_local = AgRemotePhoto.photo
        LEFT JOIN Adobe_AdditionalMetadata ON Adobe_images.id_local = Adobe_AdditionalMetadata.image
        WHERE AgRemotePhoto.url LIKE '%flickr.com%' AND AgRemotePhoto.url LIKE '%/in/set-%'
    """)

    photos_with_quotes = []
    for row in cursor.fetchall():
        lr_id, base_name, extension, path_from_root, flickr_id, xmp = row
        if xmp:
            decompressed_xmp = decompress_xmp(xmp)
            if decompressed_xmp:
                parsed_xmp = parse_xmp(decompressed_xmp)
                if parsed_xmp:
                    title = parsed_xmp.get('http://www.w3.org/1999/02/22-rdf-syntax-ns#RDF', {}).get('http://www.w3.org/1999/02/22-rdf-syntax-ns#Description', {}).get('http://purl.org/dc/elements/1.1/title', {}).get('http://www.w3.org/1999/02/22-rdf-syntax-ns#Alt', {}).get('http://www.w3.org/1999/02/22-rdf-syntax-ns#li')
                    if title and '"' in title:
                        photos_with_quotes.append({
                            'lr_id': lr_id,
                            'flickr_id': flickr_id,
                            'file_name': f"{base_name}.{extension}",
                            'file_path': path_from_root,
                            'title': title
                        })

    return photos_with_quotes

def get_flickr_photos_with_quotes(flickr):
    photos = get_flickr_photos(flickr)
    return [photo for photo in photos if '"' in photo.get('title', '')]

def main(catalog_path):
    secrets = load_secrets()
    conn = connect_to_lightroom_db(catalog_path)
    
    set_id = get_flickr_set_id(conn)
    if not set_id:
        print("Error: Could not find Flickr set ID in the Lightroom catalog.")
        conn.close()
        sys.exit(1)

    flickr = authenticate_flickr(secrets['api_key'], secrets['api_secret'])

    lr_photos_with_quotes = get_lr_photos_with_quotes(conn)
    flickr_photos_with_quotes = get_flickr_photos_with_quotes(flickr)

    conn.close()

    results = {
        'flickr_set_id': set_id,
        'lightroom_photos': lr_photos_with_quotes,
        'flickr_photos': flickr_photos_with_quotes,
        'summary': {
            'lightroom_count': len(lr_photos_with_quotes),
            'flickr_count': len(flickr_photos_with_quotes)
        }
    }

    # Print summary to console
    print(f"\nQuotes in Title Check Results:")
    print(f"Flickr Set ID: {set_id}")
    print(f"Lightroom photos with quotes in title: {results['summary']['lightroom_count']}")
    print(f"Flickr photos with quotes in title: {results['summary']['flickr_count']}")

    # Write detailed results to JSON file
    output_filename = f'quotes_in_title_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_filename, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results written to {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check-quotes-in-title.py <path_to_lightroom_catalog>")
        sys.exit(1)

    catalog_path = sys.argv[1]
    main(catalog_path)
