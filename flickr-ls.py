# Description: A script to list photos in a Flickr set or all of Flickr account.
# Usage: python flickr-ls.py --all --favorites --private
# Output will be saved to a JSONL file with details of each photo.
# Requires a secrets.json file with the following keys:
# - api_key: Your Flickr API key
# - api_secret: Your Flickr API secret
# - set_id: The ID of the Flickr set you want to list (required unless --all is specified)
#
# Known bugs: The script may not handle pagination and end-of-set correctly when
#  --private is not specified
#
import flickrapi
import json
from datetime import datetime
import argparse
import sys

def get_photo_details(flickr, photo, api_key, get_favorites=True):
    photo_id = photo.get('id')

    out = {
        'photo_id': photo_id,
        'title': photo.get('title'),
        'date_taken': photo.get('datetaken'),
        'date_upload': datetime.fromtimestamp(int(photo.get('lastupdate'))).isoformat(),
        'views': int(photo.get('views') or 0),
        'comments': int(photo.get('count_comments') or 0),
        'is_public': photo.get('ispublic')
    }

    if get_favorites:
        favorites_response = flickr.photos.getFavorites(api_key=api_key, photo_id=photo_id)
        out['favorites'] = int(favorites_response.find('photo').get('total'))

    return out

def main():
    parser = argparse.ArgumentParser(description='Flickr photo listing script')
    parser.add_argument('--all', action='store_true', help='Scan all of Flickr instead of one set')
    parser.add_argument('--favorites', action='store_true', help='Include favorites count (default: true for single set, false for --all)')
    parser.add_argument('--private', action='store_true', help='Include private photos (default: public only)')
    args = parser.parse_args()

    with open('secrets.json') as f:
        secrets = json.load(f)

    api_key = secrets['api_key']
    api_secret = secrets['api_secret']

    flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')

    per_page = 500
    page = 1
    total_photos = None

    if args.all:
        output_file = 'ls-all.jsonl'
        get_favorites = args.favorites
        search_params = {
            'user_id': 'me',
            'extras': 'date_taken,last_update,views,media,path_alias,original_format,count_comments,is_public',
            'per_page': per_page,
            'page': page
        }
        if not args.private:
            search_params['privacy_filter'] = 1  # 1 means public photos only
        print("Scanning all of Flickr...")
    else:
        set_id = secrets['set_id']
        output_file = f'ls-{set_id}.jsonl'
        get_favorites = True if args.favorites is None else args.favorites
        search_params = {
            'photoset_id': set_id,
            'extras': 'date_taken,last_update,views,media,path_alias,original_format,count_comments,is_public',
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

            # Optional: add a delay here if you're concerned about rate limiting
            # import time
            # time.sleep(1)

    print(f"Finished processing {photos_processed} photos. Results saved to {output_file}")

if __name__ == "__main__":
    main()