#!/usr/bin/env python3
"""
add-set.py: Add Photo to Flickr Set Utility

This script adds a photo to a specified Flickr set. If the set doesn't exist, it creates a new one.

Usage:
    python add-set.py --set-name 'Set Name' --id photo_id

Requirements:
    - Python 3.6+
    - flickrapi library
    - secrets.json file with:
        {
            "api_key": "your_flickr_api_key",
            "api_secret": "your_flickr_api_secret"
        }

Error Handling:
    - Handles cases where the set or photo is not found
    - Provides informative error messages for various Flickr API errors
"""

import argparse
import json
import sys
import flickrapi

def load_secrets():
    with open('secrets.json') as f:
        return json.load(f)

def authenticate_flickr(api_key, api_secret):
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
    if not flickr.token_valid(perms='write'):
        flickr.get_request_token(oauth_callback='oob')
        authorize_url = flickr.auth_url(perms='write')
        print(f"Please authorize this app: {authorize_url}")
        verifier = input('Verifier code: ')
        flickr.get_access_token(verifier)
    return flickr

def get_or_create_set(flickr, set_name):
    try:
        # Try to find the set
        sets = flickr.photosets.getList()
        for photoset in sets['photosets']['photoset']:
            if photoset['title']['_content'] == set_name:
                return photoset['id']

        # If set not found, create a new one
        print(f"Set '{set_name}' not found. Creating new set.")
        # We need a photo to create a set, so we'll use the user's first photo
        first_photo = flickr.people.getPhotos(user_id='me', per_page=1)['photos']['photo'][0]
        new_set = flickr.photosets.create(title=set_name, primary_photo_id=first_photo['id'])
        return new_set['photoset']['id']
    except flickrapi.exceptions.FlickrError as e:
        print(f"Error getting or creating Flickr set: {e}")
        sys.exit(1)

def add_photo_to_set(flickr, set_id, photo_id):
    try:
        flickr.photosets.addPhoto(photoset_id=set_id, photo_id=photo_id)
        print(f"Successfully added photo {photo_id} to set.")
    except flickrapi.exceptions.FlickrError as e:
        if 'Photo not found' in str(e):
            print(f"Error: Photo with ID {photo_id} not found.")
        elif 'Photo already in set' in str(e):
            print(f"Note: Photo {photo_id} is already in the set.")
        else:
            print(f"Error adding photo to set: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Add a photo to a Flickr set")
    parser.add_argument('--set-name', required=True, help="Name of the Flickr set")
    parser.add_argument('--id', required=True, help="ID of the photo to add")
    args = parser.parse_args()

    secrets = load_secrets()
    flickr = authenticate_flickr(secrets['api_key'], secrets['api_secret'])

    try:
        set_id = get_or_create_set(flickr, args.set_name)
        add_photo_to_set(flickr, set_id, args.id)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()