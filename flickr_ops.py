"""
flickr_operations.py: Module for Flickr-specific operations including photo listing and retrieval

This module handles interactions with the Flickr API, including
authentication, photo information retrieval, and photo listing functionality.
It also includes utilities for adding and removing photos from Flickr sets.

"""

import os
import json
import flickrapi
import argparse
from datetime import datetime

def sync_flickr_set(flickr, photos_to_add, photos_to_remove, set_id, debug=False):
    """
    Synchronize a Flickr set with Lightroom by adding and removing photos.

    Args:
    flickr (flickrapi.FlickrAPI): Authenticated Flickr API object
    photos_to_add (list): List of photo IDs to add to the Flickr set
    photos_to_remove (list): List of photo IDs to remove from the Flickr set
    set_id (str): ID of the Flickr set to synchronize
    debug (bool): Whether to print debug information

    Returns:
    tuple: Lists of successfully added and removed photo IDs
    """
    added_photos = []
    removed_photos = []

    for photo_id in photos_to_add:
        if debug:
            print(f"Attempting to add photo {photo_id} to set {set_id}")
        try:
            add_to_managed_set(flickr, photo_id, set_id)
            added_photos.append(photo_id)
        except Exception as e:
            print(f"Failed to add photo {photo_id} to set {set_id}: {str(e)}")

    for photo_id in photos_to_remove:
        if debug:
            print(f"Attempting to remove photo {photo_id} from set {set_id}")
        try:
            remove_from_set(flickr, photo_id, set_id)
            removed_photos.append(photo_id)
        except Exception as e:
            print(f"Failed to remove photo {photo_id} from set {set_id}: {str(e)}")

    return added_photos, removed_photos

def remove_from_set(flickr: flickrapi.FlickrAPI, photo_id: str, set_id: str) -> None:
    """
    Remove a photo from a Flickr set.

    Args:
    flickr (flickrapi.FlickrAPI): Authenticated Flickr API object
    photo_id (str): ID of the photo to remove
    set_id (str): ID of the set to remove the photo from

    Raises:
    Exception: If there's an error removing the photo from the set
    """
    try:
        flickr.photosets.removePhoto(api_key=flickr.api_key, photoset_id=set_id, photo_id=photo_id)
    except Exception as e:
        raise Exception(f"Error removing photo {photo_id} from set {set_id}: {str(e)}")

def sync_flickr_set(flickr, photos_to_add, photos_to_remove, set_id, debug=False):
    added_photos = []
    removed_photos = []
    for photo_id in photos_to_add:
        if debug:
            print(f"Attempting to add photo {photo_id} to set {set_id}")
        try:
            add_to_managed_set(flickr, photo_id, set_id)
            added_photos.append(photo_id)
        except Exception as e:
            print(f"Failed to add photo {photo_id} to set {set_id}: {str(e)}")

    for photo_id in photos_to_remove:
        if debug:
            print(f"Attempting to remove photo {photo_id} from set {set_id}")
        try:
            remove_from_set(flickr, photo_id, set_id)
            removed_photos.append(photo_id)
        except Exception as e:
            print(f"Failed to remove photo {photo_id} from set {set_id}: {str(e)}")

    return added_photos, removed_photos

def get_all_photos_in_set(flickr, set_id):
    """Fetch all photos in a Flickr set, handling pagination."""
    photos = []
    page = 1
    per_page = 500  # Maximum allowed by Flickr API

    while True:
        response = flickr.photosets.getPhotos(photoset_id=set_id, page=page, per_page=per_page)
        photos.extend(response['photoset']['photo'])

        if page >= response['photoset']['pages']:
            break

        page += 1

    return photos

def authenticate_flickr(api_key, api_secret):
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
    if not flickr.token_valid(perms='read'):
        flickr.get_request_token(oauth_callback='oob')
        authorize_url = flickr.auth_url(perms='read')
        print(f"Please authorize this app: {authorize_url}")
        verifier = input('Verifier code: ')
        flickr.get_access_token(verifier)
    return flickr

def add_to_managed_set(flickr, photo_id, set_id):
    """Add a photo to a managed Flickr set."""
    try:
        flickr.photosets.addPhoto(photoset_id=set_id, photo_id=photo_id)
        print(f"Added photo {photo_id} to managed set {set_id}")
    except flickrapi.exceptions.FlickrError as e:
        print(f"Error adding photo {photo_id} to managed set {set_id}: {str(e)}")

def get_flickr_photos(flickr):
    if os.path.exists('ls-all.jsonl'):
        print("Reading photo list from ls-all.jsonl...")
        photos = []
        with open('ls-all.jsonl', 'r') as f:
            for line in f:
                photo = json.loads(line)
                photos.append(photo)
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

def get_photo_details(flickr, photo, api_key, get_favorites=True):

    out = photo

    if get_favorites:
        favorites_response = flickr.photos.getFavorites(api_key=api_key, photo_id=photo['id'])
        out['favorites'] = int(favorites_response.find('photo').get('total'))

    return out

def list_photos(flickr, api_key, api_secret, args):
    per_page = 500
    page = 1
    total_photos = None

    if args.all:
        output_file = 'ls-all.jsonl'
        get_favorites = args.favorites
        search_params = {
            'user_id': 'me',
            'extras': 'date_taken,last_update,views,media,path_alias,original_format,count_comments,ispublic',
            'per_page': per_page,
            'page': page
        }
        if not args.private:
            search_params['privacy_filter'] = 1  # 1 means public photos only
        print("Scanning all of Flickr...")
    else:
        set_id = args.set_id
        output_file = f'ls-{set_id}.jsonl'
        get_favorites = True if args.favorites is None else args.favorites
        search_params = {
            'photoset_id': set_id,
            'extras': 'date_taken,last_update,views,media,path_alias,original_format,count_comments,ispublic',
            'per_page': per_page,
            'page': page
        }
        print(f"Scanning Flickr set with ID: {set_id}")

    print(f"Output will be saved to: {output_file}")
    print(f"Fetching favorites: {'Yes' if get_favorites else 'No'}")
    print(f"Including private photos: {'Yes' if args.private else 'No'}")

    photos_processed = 0
    with open(output_file, 'w') as outfile:
        while total_photos is None or photos_processed < total_photos:
            if args.all:
                response = flickr.photos.search(**search_params)
                photos = response['photos']['photo']
                if total_photos is None:
                    total_photos = int(response['photos']['total'])
            else:
                response = flickr.photosets.getPhotos(**search_params)
                photos = response['photoset']['photo']
                if total_photos is None:
                    total_photos = int(response['photoset']['total'])

            if not photos:
                break

            for photo in photos:
                if args.private or photo['ispublic'] == 1:
                    photo_details = get_photo_details(flickr, photo, api_key, get_favorites)
                    json.dump(photo_details, outfile)
                    outfile.write('\n')
                    photos_processed += 1

            print(f"Processed page {page} of {(total_photos + per_page - 1) // per_page}: {photos_processed} of {total_photos} photos")

            page += 1
            search_params['page'] = page

    print(f"Finished processing {photos_processed} photos. Results saved to {output_file}")

def delete_flickr_photo(flickr, photo_id):
    """
    Delete a photo from Flickr.

    :param flickr: Authenticated Flickr API object
    :param photo_id: ID of the photo to delete
    :return: True if deletion was successful, False otherwise
    """
    try:
        # Attempt to delete the photo
        response = flickr.photos.delete(photo_id=photo_id)

        # Check if the deletion was successful
        if response['stat'] == 'ok':
            print(f"Successfully deleted photo with ID: {photo_id}")
            return True
        else:
            print(f"Failed to delete photo with ID: {photo_id}")
            return False
    except flickrapi.exceptions.FlickrError as e:
        print(f"Error deleting photo with ID {photo_id}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Flickr operations script')
    parser.add_argument('--ls', action='store_true', help='List photos (use with additional arguments)')
    parser.add_argument('--all', action='store_true', help='Scan all of Flickr instead of one set')
    parser.add_argument('--favorites', action='store_true', help='Include favorites count (default: true for single set, false for --all)')
    parser.add_argument('--private', action='store_true', help='Include private photos (default: public only)')
    parser.add_argument('--set-id', help='The ID of the Flickr set to list (required unless --all is specified)')
    args = parser.parse_args()

    with open('secrets.json') as f:
        secrets = json.load(f)

    api_key = secrets['api_key']
    api_secret = secrets['api_secret']

    flickr = authenticate_flickr(api_key, api_secret)

    if args.ls:
        if not args.all and not args.set_id:
            print("Error: Either --all or --set-id must be specified when using --ls")
            return
        list_photos(flickr, api_key, api_secret, args)
    else:
        # Add other functionalities here
        print("No operation specified. Use --ls to list photos.")

if __name__ == "__main__":
    main()
