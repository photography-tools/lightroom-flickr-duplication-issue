"""
lr-flickr-instanceid-report-yaml.py: Generate a YAML report of InstanceIDs for Flickr-published photos

This script connects to a Lightroom catalog and generates a report listing the
xmp.RDF.Description.@InstanceID for all photos that have been published to Flickr.

Usage:
    python lr-flickr-instanceid-report-yaml.py <path_to_lightroom_catalog>

Arguments:
    path_to_lightroom_catalog: Path to the Lightroom catalog file (.lrcat)

Output:
    Writes a YAML file with the report results, using filenames as primary keys.
"""

import sqlite3
import sys
import os
from datetime import datetime
import zlib
import struct
from lxml import etree
import yaml

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
    return decompressed_data

def flatten_xml(elem, prefix=''):
    result = {}
    for child in elem:
        name = child.tag.split('}')[-1]  # Remove namespace
        full_name = f"{prefix}.{name}" if prefix else name
        if len(child) > 0:
            result.update(flatten_xml(child, full_name))
        else:
            result[full_name] = child.text if child.text else ''
    for name, value in elem.attrib.items():
        name = name.split('}')[-1]  # Remove namespace
        full_name = f"{prefix}.@{name}" if prefix else f"@{name}"
        result[full_name] = value
    return result

def parse_xmp(xmp_data):
    try:
        root = etree.fromstring(xmp_data)
        return flatten_xml(root)
    except Exception as e:
        print(f"Error parsing XMP data: {e}")
        return None

def get_flickr_published_photos(conn):
    cursor = conn.cursor()
    query = """
    SELECT
        AgLibraryFile.id_local,
        AgLibraryFile.baseName,
        AgLibraryFile.extension,
        AgLibraryFolder.pathFromRoot,
        AgRemotePhoto.remoteId,
        Adobe_AdditionalMetadata.xmp
    FROM AgLibraryFile
    JOIN AgLibraryFolder ON AgLibraryFile.folder = AgLibraryFolder.id_local
    JOIN Adobe_images ON AgLibraryFile.id_local = Adobe_images.rootFile
    LEFT JOIN AgRemotePhoto ON Adobe_images.id_local = AgRemotePhoto.photo
    LEFT JOIN Adobe_AdditionalMetadata ON Adobe_images.id_local = Adobe_AdditionalMetadata.image
    WHERE AgRemotePhoto.remoteId IS NOT NULL
    """
    cursor.execute(query)
    return cursor.fetchall()

def generate_report(catalog_path):
    conn = connect_to_lightroom_db(catalog_path)
    photos = get_flickr_published_photos(conn)
    conn.close()

    report_data = {}
    for photo in photos:
        file_id, base_name, extension, path, remote_id, xmp = photo
        full_path = os.path.join(path, f"{base_name}.{extension}")
        filename = os.path.basename(full_path)

        xmp_data = {}
        if xmp:
            decompressed_xmp = decompress_xmp(xmp)
            if decompressed_xmp:
                xmp_data = parse_xmp(decompressed_xmp)

        instance_id = xmp_data.get('RDF.Description.@InstanceID')

        # Extract tags from XMP data
        tags = []
        for key in xmp_data:
            if key.startswith('RDF.Description.subject.Bag.li') or key.startswith('RDF.Description.dc:subject.rdf:Bag.rdf:li'):
                tags.append(xmp_data[key])

        report_data[filename] = {
            'file_id': file_id,
            'file_path': full_path,
            'flickr_id': remote_id,
            'xmp.RDF.Description.@InstanceID': instance_id,
            'remote_id': remote_id,
            'tags': tags  # Added this line to include tags
        }

    # Write report to YAML
    output_filename = f'flickr_instanceid_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml'
    with open(output_filename, 'w', encoding='utf-8') as yamlfile:
        yaml.dump(report_data, yamlfile, default_flow_style=False, allow_unicode=True)

    print(f"Report generated: {output_filename}")
    print(f"Total Flickr-published photos: {len(report_data)}")
    print(f"Photos with InstanceID: {sum(1 for photo in report_data.values() if photo['xmp.RDF.Description.@InstanceID'])}")
    print(f"Photos without InstanceID: {sum(1 for photo in report_data.values() if not photo['xmp.RDF.Description.@InstanceID'])}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python lr-flickr-instanceid-report-yaml.py <path_to_lightroom_catalog>")
        sys.exit(1)

    catalog_path = sys.argv[1]
    generate_report(catalog_path)
