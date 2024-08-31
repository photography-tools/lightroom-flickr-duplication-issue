"""
flickr_operations.py: Module for Flickr-specific operations in the audit process

This module handles interactions with the Flickr API, including
authentication and photo information retrieval.
"""

import os
import json
import flickrapi

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
