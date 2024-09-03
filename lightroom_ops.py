"""
lightroom_operations.py: Module for Lightroom-specific operations in the audit process

This module handles interactions with the Lightroom catalog, including
database connections and comprehensive photo information extraction.
"""

from collections import defaultdict
import sqlite3
import struct
import zlib
from lxml import etree
import base64
import json

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
        return etree_to_dict(root)
    except Exception as e:
        print(f"Error parsing XMP data: {e}")
        return None

def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

def get_table_data(conn, table_name, id_column, id_value):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE {id_column} = ?", (id_value,))
    columns = [description[0] for description in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(columns, row))
    return None

def get_lr_photos(conn, set_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            Adobe_images.id_local,
            Adobe_images.id_global,
            AgLibraryFile.id_local AS file_id_local,
            Adobe_AdditionalMetadata.id_local AS metadata_id_local,
            AgRemotePhoto.remoteId
        FROM Adobe_images
        JOIN AgLibraryFile ON Adobe_images.rootFile = AgLibraryFile.id_local
        JOIN AgRemotePhoto ON Adobe_images.id_local = AgRemotePhoto.photo
        LEFT JOIN Adobe_AdditionalMetadata ON Adobe_images.id_local = Adobe_AdditionalMetadata.image
        WHERE AgRemotePhoto.url LIKE ? AND AgRemotePhoto.url LIKE ?
    """, (f'%flickr.com%', f'%/in/set-{set_id}%'))

    lr_photos = []
    for row in cursor.fetchall():
        lr_id, lr_global_id, file_id_local, metadata_id_local, flickr_id = row

        adobe_images_data = get_table_data(conn, "Adobe_images", "id_local", lr_id)
        ag_library_file_data = get_table_data(conn, "AgLibraryFile", "id_local", file_id_local)
        adobe_additional_metadata_data = get_table_data(conn, "Adobe_AdditionalMetadata", "id_local", metadata_id_local)

        xmp_data = None
        parsed_xmp = None
        if adobe_additional_metadata_data and adobe_additional_metadata_data.get('xmp'):
            xmp_data = decompress_xmp(adobe_additional_metadata_data['xmp'])
            if xmp_data:
                xmp_data = parse_xmp(xmp_data)
                adobe_additional_metadata_data['xmp'] = xmp_data

        lr_photos.append({
            "lr_id": lr_id,
            "lr_global_id": lr_global_id,
            "lr_remote_id": flickr_id,
            "adobe_images": adobe_images_data,
            "ag_library_file": ag_library_file_data,
            "adobe_additional_metadata": adobe_additional_metadata_data,
        })

    return lr_photos

def get_all_lr_photos(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            Adobe_images.id_local,
            Adobe_images.id_global,
            AgLibraryFile.id_local AS file_id_local,
            Adobe_AdditionalMetadata.id_local AS metadata_id_local,
            AgRemotePhoto.remoteId
        FROM Adobe_images
        JOIN AgLibraryFile ON Adobe_images.rootFile = AgLibraryFile.id_local
        LEFT JOIN AgRemotePhoto ON Adobe_images.id_local = AgRemotePhoto.photo
        LEFT JOIN Adobe_AdditionalMetadata ON Adobe_images.id_local = Adobe_AdditionalMetadata.image
    """)

    lr_photos = []
    for row in cursor.fetchall():
        lr_id, lr_global_id, file_id_local, metadata_id_local, flickr_id = row

        adobe_images_data = get_table_data(conn, "Adobe_images", "id_local", lr_id)
        ag_library_file_data = get_table_data(conn, "AgLibraryFile", "id_local", file_id_local)
        adobe_additional_metadata_data = get_table_data(conn, "Adobe_AdditionalMetadata", "id_local", metadata_id_local)

        xmp_data = None
        parsed_xmp = None
        if adobe_additional_metadata_data and adobe_additional_metadata_data.get('xmp'):
            xmp_data = decompress_xmp(adobe_additional_metadata_data['xmp'])
            if xmp_data:
                xmp_data = parse_xmp(xmp_data)
                adobe_additional_metadata_data['xmp'] = xmp_data

        lr_photos.append({
            "lr_id": lr_id,
            "lr_global_id": lr_global_id,
            "lr_remote_id": flickr_id,
            "adobe_images": adobe_images_data,
            "ag_library_file": ag_library_file_data,
            "adobe_additional_metadata": adobe_additional_metadata_data,
        })

    return lr_photos

def get_flickr_sets(conn):
    """Get all Flickr sets from the Lightroom database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT SUBSTRING(url, INSTR(url, 'set-') + 4) as set_id
        FROM AgRemotePhoto
        WHERE url LIKE '%flickr.com%' AND url LIKE '%/in/set-%'
    """)
    return [row[0] for row in cursor.fetchall()]

