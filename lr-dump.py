"""
lr-dump.py: Utility to dump and compare Lightroom catalog data for specified images

This script connects to a Lightroom catalog, finds images matching specified path substrings or remote IDs,
and outputs a flat comparison of all fields to a Markdown file with tables.

Features:
- Dumps detailed Lightroom catalog data for specified images
- Supports multiple path substrings and remote IDs for flexible image selection
- Flattens XMP hierarchy (e.g., a/b/c becomes a.b.c)
- Provides a flat comparison of all fields across images
- Separates fields with the same values across all images into a distinct table
- Outputs results in Markdown format for easy reading and further processing

Usage:
    python lr-dump.py <path_to_lightroom_catalog> [--filename <substring1> ...] [--remote <remote_id1> ...]

Arguments:
    path_to_lightroom_catalog: Path to the Lightroom catalog file (.lrcat)
    --filename: Substring(s) to match against image file paths. Can be specified multiple times.
    --remote: Remote ID(s) to match against AgRemotePhoto.remoteId. Can be specified multiple times.

Output:
    Writes detailed results to a Markdown file with tables for field comparisons.
"""

import sqlite3
import argparse
from lxml import etree
import zlib
import struct
from datetime import datetime
import os
from collections import defaultdict

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
        return flatten_xml(root)
    except Exception as e:
        print(f"Error parsing XMP data: {e}")
        return None

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

def get_image_data(conn, path_substrings, remote_ids):
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if path_substrings:
        where_clauses.extend(["AgLibraryFolder.pathFromRoot || '/' || AgLibraryFile.baseName || '.' || AgLibraryFile.extension LIKE ?" for _ in path_substrings])
        params.extend([f'%{substring}%' for substring in path_substrings])

    if remote_ids:
        where_clauses.extend(["AgRemotePhoto.remoteId = ?" for _ in remote_ids])
        params.extend(remote_ids)

    where_clause = " OR ".join(where_clauses)

    query = f"""
    SELECT
        Adobe_images.*,
        AgLibraryFile.*,
        AgLibraryFolder.pathFromRoot,
        AgRemotePhoto.remoteId,
        Adobe_AdditionalMetadata.xmp,
        AgLibraryPublishedCollection.remoteCollectionId,
        AgLibraryPublishedCollection.publishedUrl
    FROM Adobe_images
    JOIN AgLibraryFile ON Adobe_images.rootFile = AgLibraryFile.id_local
    JOIN AgLibraryFolder ON AgLibraryFile.folder = AgLibraryFolder.id_local
    LEFT JOIN AgRemotePhoto ON Adobe_images.id_local = AgRemotePhoto.photo
    LEFT JOIN Adobe_AdditionalMetadata ON Adobe_images.id_local = Adobe_AdditionalMetadata.image
    LEFT JOIN AgLibraryPublishedCollectionImage ON Adobe_images.id_local = AgLibraryPublishedCollectionImage.image
    LEFT JOIN AgLibraryPublishedCollection ON AgLibraryPublishedCollectionImage.collection = AgLibraryPublishedCollection.id_local
    WHERE {where_clause}
    """

    cursor.execute(query, params)

    columns = [description[0] for description in cursor.description]
    images = []

    for row in cursor.fetchall():
        image_data = dict(zip(columns, row))

        # Construct full file path
        image_data['full_file_path'] = os.path.join(
            image_data['pathFromRoot'],
            f"{image_data['baseName']}.{image_data['extension']}"
        )

        # Parse XMP data if available
        if image_data.get('xmp'):
            decompressed_xmp = decompress_xmp(image_data['xmp'])
            if decompressed_xmp:
                xmp_data = parse_xmp(decompressed_xmp)
                if xmp_data:
                    image_data.update({f"xmp.{k}": v for k, v in xmp_data.items()})

        # Remove the original compressed XMP data
        image_data.pop('xmp', None)

        images.append(image_data)

    return images

def generate_markdown_table(headers, data):
    # Create the header row
    markdown = "| " + " | ".join(headers) + " |\n"
    # Create the separator row
    markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    # Create data rows
    for row in data:
        markdown += "| " + " | ".join(str(cell) for cell in row) + " |\n"
    return markdown

def generate_markdown_output(images):
    markdown = f"# Lightroom Catalog Dump\n\n"
    markdown += f"Date: {datetime.now().isoformat()}\n\n"

    # Get all unique fields
    all_fields = set()
    for image in images:
        all_fields.update(image.keys())

    # Separate fields with same values and different values
    same_value_fields = []
    diff_value_fields = []

    for field in sorted(all_fields):
        values = [str(image.get(field, '')) for image in images]
        if len(set(values)) == 1:
            same_value_fields.append((field, values[0]))
        else:
            diff_value_fields.append((field, values))

    # Generate table for fields with same values
    markdown += "## Fields with Same Values Across All Images\n\n"
    headers = ['Field', 'Value']
    data = same_value_fields
    markdown += generate_markdown_table(headers, data)
    markdown += "\n"

    # Generate table for fields with different values
    markdown += "## Fields with Different Values\n\n"
    headers = ['Field'] + [f"Image {i+1}" for i in range(len(images))]
    data = [[field] + values for field, values in diff_value_fields]
    markdown += generate_markdown_table(headers, data)
    markdown += "\n"

    # Add a section with full file paths for reference
    markdown += "## Image File Paths\n\n"
    for i, image in enumerate(images):
        markdown += f"Image {i+1}: {image['full_file_path']}\n"

    return markdown

def main(catalog_path, path_substrings, remote_ids):
    conn = connect_to_lightroom_db(catalog_path)
    images = get_image_data(conn, path_substrings, remote_ids)
    conn.close()

    markdown_output = generate_markdown_output(images)

    # Write results to Markdown file
    output_filename = f'lr_dump_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(markdown_output)

    print(f"Dump completed. {len(images)} images found.")
    print(f"Results written to {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dump Lightroom catalog data for specified images")
    parser.add_argument("catalog_path", help="Path to the Lightroom catalog file (.lrcat)")
    parser.add_argument("--filename", action='append', help="Substring to match against image file paths. Can be specified multiple times.")
    parser.add_argument("--remote", action='append', help="Remote ID to match against AgRemotePhoto.remoteId. Can be specified multiple times.")

    args = parser.parse_args()

    if not args.path_substring and not args.remote:
        parser.error("At least one of --filename or --remote must be specified.")

    main(args.catalog_path, args.path_substring, args.remote)
