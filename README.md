# Lightroom-Flickr Synchronization Fix

## The Issue

This project addresses a long-standing issue with Adobe Lightroom's Flickr plugin that causes duplicate photo uploads due to improper handling of special characters like double quotes (") and backslashes (\) at the end of photo titles.

When these special characters are present, they break the parsing of the Flickr API response in the Lightroom plugin. As a result, the plugin mishandles affected photos and others in the same batch (up to 500 photos), leading to duplicate uploads instead of updates to existing photos. A single problematic photo can cause up to 500 uploads to fail, creating duplicates.

These scripts were created to troubleshoot and fix the issue. They are designed to audit discrepancies between Lightroom catalogs and Flickr photosets, identify duplicates, and provide methods to resolve the issues. While comprehensive, these tools were used for one-time fixes and have not been maintained or tested beyond their initial use.

More information about the Lightroom plugin bug can be found in this forum post:
https://community.adobe.com/t5/lightroom-classic-discussions/lightroom-creates-duplicates-when-republishing-to-flickr/m-p/9695954

## Solution Overview

The solution, which is really a long-term "workaround and avoid", involves:

1. Identifying affected photos
2. Removing duplicate uploads from Flickr
3. Correcting Lightroom catalog entries to repoint to the original uploads
4. Preventing future occurrences by sanitizing photo titles

## Scripts

1. `audit_utils.py`, `flickr_ops.py`,`lightroom_ops.py` : Utility functions for the other scripts. Run `flickr_ops.py --all` to create a Flickr cache file (`ls-all.json`) that speeds up other scripts.

2. `clear-flickr-titles.py`: Clears Flickr photo titles in Lightroom published sets and optionally resets them to the photo IDs.

3. `delete-orphans.py`: Identifies and soft-deletes photos present in a Lightroom-managed Flickr album but not in the corresponding Lightroom-Flickr publish collection.

4. `lightroom-flickr-audit.py`: Main script for Lightroom-Flickr Audit. Performs a comprehensive audit between Lightroom catalogs and Flickr sets.

5. `lr-check-duplicate-identifiers.py`: Utility to find and report photos with duplicate InstanceID or DocumentID values. There was an attempt to use these IDs for photo de-deplication. It was found that these IDs are not reliable.

6. `lr-dump.py`: Utility to dump and compare Lightroom catalog data for specified images. This was useful for troubleshooting and trying to figure out how different images EXIF, IPTC, and XMP tags compare.

7. `merge.py`: One-at-a-time fix to repoint a single photo from LR publish collection to a different Flickr photo. Useful when manually undoing duplicates.

8. `swap.py`: Swaps Flickr photo references for two photos in the Lightroom catalog. This is useful sometimes to swap the RAW and the JPEG before deleting the JPEG, or to manually deal with quasi-duplicates.

## Prerequisites

- Python 3.6+
- `flickrapi` library
- `lxml` library
- Flickr API key and secret
- Adobe Lightroom catalog with the Flickr export plugin installed
- SQLite3 (usually pre-installed with Python)
- DB Browser for SQLite (for manual database inspection if needed)

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/flickr-lightroom-fix.git
   cd flickr-lightroom-fix
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `secrets.json` file in the project root with the necessary credentials and paths:
   ```json
   {
     "api_key": "your_flickr_api_key",
     "api_secret": "your_flickr_api_secret",
     "set_id": "your_managed_flickr_set_id",
     "lrcat_file_path": "/path/to/your/lightroom_catalog.lrcat"
   }
   ```

## Configuration

Most scripts read configuration from the `secrets.json` file. Some scripts accept additional command-line arguments. Use the `--help` flag with any script to see available options.

## Usage Notes

These scripts should be used carefully and in a specific sequence depending on the issue you're addressing. Always run scripts in dry-run mode first (usually by omitting the `--force` flag) to verify actions before applying changes.

All current scripts in this toolkit are designed to interact directly with the Lightroom catalog file and do not require manual data extraction steps. They use SQLite connections to read from and write to the Lightroom database as needed.

## Caution

These scripts were created for specific one-time fixes and can make significant changes to both the Lightroom catalog and Flickr account. Always backup your Lightroom catalog before running any scripts. REVIEW THE CODE. USE AT YOUR OWN RISK.

## lr-sdk-13.5 folder

This contains a copy of the sample Flickr plugin from Adobe. This appears to be an older version of the current plugin, but suffers of the same bug, and was instrumental for understanding what's going on.

## License

GNU v3 where applicable.
