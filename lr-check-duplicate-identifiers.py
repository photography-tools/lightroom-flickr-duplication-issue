"""
audit_dup_id.py: Utility to find and report photos with duplicate InstanceID or DocumentID values

This script directly scans the Lightroom catalog, identifies photos that have
duplicate values for the specified ID type in their XMP metadata, and outputs the results to a YAML file.
For cases with exactly two duplicates, it performs a full comparison of all database and XML fields.

In the script author's own catalog, it was discovered that the InstanceID field has
massive duplication and it's not a useful identification field for most purposes.

Usage:
    python audit_dup_id.py <path_to_lightroom_catalog> --attr {iid|did}

Arguments:
    path_to_lightroom_catalog: Path to the Lightroom catalog file (.lrcat)
    --attr: Specify which ID to check for duplicates (iid for InstanceID, did for DocumentID)

Output:
    Writes detailed results to a YAML file and prints a summary to the console.
"""

import sqlite3
import sys
import argparse
from collections import defaultdict
import struct
import zlib
from lxml import etree
import yaml
from datetime import datetime
import os

# Custom YAML representer for lxml.etree._ElementUnicodeResult
def represent_unicode_result(dumper, data):
    return dumper.represent_str(str(data))

yaml.add_representer(etree._ElementUnicodeResult, represent_unicode_result)

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

def parse_xmp(xmp_data):
    try:
        root = etree.fromstring(xmp_data)
        namespaces = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'xmp': 'http://ns.adobe.com/xap/1.0/',
            'xmpMM': 'http://ns.adobe.com/xap/1.0/mm/'
        }

        # Extract all XML data
        xml_data = {}
        for elem in root.iter():
            if elem.tag.startswith('{'):
                ns, tag = elem.tag[1:].split('}')
                if elem.text and elem.text.strip():
                    xml_data[f"{{{ns}}}{tag}"] = elem.text.strip()
            for name, value in elem.attrib.items():
                if name.startswith('{'):
                    ns, attr = name[1:].split('}')
                    xml_data[f"{{{ns}}}{attr}"] = value
                else:
                    xml_data[name] = value

        instance_id = xml_data.get('{http://ns.adobe.com/xap/1.0/mm/}InstanceID')
        document_id = xml_data.get('{http://ns.adobe.com/xap/1.0/mm/}DocumentID')

        return instance_id, document_id, xml_data
    except Exception as e:
        print(f"Error parsing XMP data: {e}")
        return None, None, {}

def get_photos_with_ids(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            Adobe_images.*,
            AgLibraryFile.*,
            AgLibraryFolder.pathFromRoot,
            AgRemotePhoto.remoteId,
            Adobe_AdditionalMetadata.xmp
        FROM Adobe_images
        JOIN AgLibraryFile ON Adobe_images.rootFile = AgLibraryFile.id_local
        JOIN AgLibraryFolder ON AgLibraryFile.folder = AgLibraryFolder.id_local
        LEFT JOIN AgRemotePhoto ON Adobe_images.id_local = AgRemotePhoto.photo
        LEFT JOIN Adobe_AdditionalMetadata ON Adobe_images.id_local = Adobe_AdditionalMetadata.image
    """)

    columns = [description[0] for description in cursor.description]
    photos = []
    for row in cursor.fetchall():
        photo_data = dict(zip(columns, row))

        instance_id, document_id, xml_data = None, None, {}
        if photo_data['xmp']:
            decompressed_xmp = decompress_xmp(photo_data['xmp'])
            if decompressed_xmp:
                instance_id, document_id, xml_data = parse_xmp(decompressed_xmp)

        full_file_path = os.path.join(photo_data['pathFromRoot'], f"{photo_data['baseName']}.{photo_data['extension']}" if photo_data['extension'] else photo_data['baseName'])

        photo_data['file_path'] = full_file_path
        photo_data['instance_id'] = instance_id
        photo_data['document_id'] = document_id
        photo_data['xml_data'] = xml_data

        photos.append(photo_data)

    return photos

def compare_photos(photo1, photo2):
    differences = {}

    # Compare database fields
    for key in set(photo1.keys()) | set(photo2.keys()):
        if key not in ['xmp', 'xml_data']:  # Exclude raw XMP and parsed XML data from this comparison
            if photo1.get(key) != photo2.get(key):
                differences[key] = {
                    'photo1': photo1.get(key),
                    'photo2': photo2.get(key)
                }

    # Compare XML data
    xml_differences = {}
    all_xml_keys = set(photo1['xml_data'].keys()) | set(photo2['xml_data'].keys())
    for key in all_xml_keys:
        if photo1['xml_data'].get(key) != photo2['xml_data'].get(key):
            xml_differences[key] = {
                'photo1': photo1['xml_data'].get(key),
                'photo2': photo2['xml_data'].get(key)
            }

    if xml_differences:
        differences['xml_data'] = xml_differences

    return differences

def main(catalog_path, id_type):
    conn = connect_to_lightroom_db(catalog_path)
    photos = get_photos_with_ids(conn)
    conn.close()

    # Group photos by the specified ID type
    id_groups = defaultdict(list)
    for photo in photos:
        id_value = photo[id_type]
        if id_value:
            id_groups[id_value].append(photo)

    # Prepare results for YAML output
    results = {
        'audit_date': datetime.now().isoformat(),
        'catalog_path': catalog_path,
        'id_type_for_deduplication': 'InstanceID' if id_type == 'instance_id' else 'DocumentID',
        'duplicate_ids': [],
        'summary': {}
    }

    # Find duplicates and perform full comparison for pairs
    duplicates_found = False
    for id_value, group in id_groups.items():
        if len(group) > 1:
            duplicates_found = True
            duplicate_entry = {
                'id': id_value,
                'count': len(group),
                'photos': group
            }

            if len(group) == 2:
                differences = compare_photos(group[0], group[1])
                if differences:
                    duplicate_entry['differences'] = differences

            results['duplicate_ids'].append(duplicate_entry)

    # Prepare summary
    total_photos = len(photos)
    photos_with_id = sum(1 for photo in photos if photo[id_type])
    results['summary'] = {
        'total_photos': total_photos,
        f'photos_with_{id_type}': photos_with_id,
        f'photos_without_{id_type}': total_photos - photos_with_id,
        'duplicate_groups_count': len(results['duplicate_ids'])
    }

    # Write results to YAML file
    output_filename = f'lr_flickr_audit_results_{id_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml'
    with open(output_filename, 'w') as f:
        yaml.dump(results, f, default_flow_style=False)

    # Print summary to console
    print(f"\nAudit Results Summary (Deduplication based on {results['id_type_for_deduplication']}):")
    print(f"Total photos scanned: {total_photos}")
    print(f"Photos with {results['id_type_for_deduplication']}: {photos_with_id}")
    print(f"Photos without {results['id_type_for_deduplication']}: {total_photos - photos_with_id}")
    print(f"Number of duplicate {results['id_type_for_deduplication']} groups: {len(results['duplicate_ids'])}")
    print(f"\nDetailed results written to {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit Lightroom catalog for duplicate InstanceIDs or DocumentIDs")
    parser.add_argument("catalog_path", help="Path to the Lightroom catalog file (.lrcat)")
    parser.add_argument("--attr", choices=['iid', 'did'], required=True, help="Specify which ID to check for duplicates (iid for InstanceID, did for DocumentID)")

    args = parser.parse_args()

    id_type = 'instance_id' if args.attr == 'iid' else 'document_id'
    main(args.catalog_path, id_type)
