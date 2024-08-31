# Scripts for Troubleshooting Lightroom-Flickr Plugin Issue

This repository contains a collection of Python scripts I developed to try to troubleshoot
and fix an issue with duplicate uploads caused by the Flickr plugin for Adobe Lightroom. These tools were created to troubleshoot and fix the problem, and are not intended for regular use. I'm publishing them here for future reference in case a similar issue arises.

## Table of Contents

- [Overview](#overview)
- [Scripts](#scripts)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Configuration](#configuration)
- [Usage Notes](#usage-notes)
- [Lightroom Data Extraction](#lightroom-data-extraction)
- [Caution](#caution)
- [License](#license)

## Overview

These scripts were created in response to a mass duplicate upload event caused by a malfunction in the Lightroom Flickr plugin. They were designed to audit the discrepancies between my Lightroom catalog and Flickr photosets, identify the duplicates, and provide methods to resolve the issues. While comprehensive, these tools were used for a one-time fix and have not been maintained or tested beyond their initial use.

## Scripts

1. `add-set.py`: Adds a photo to a specified Flickr set, creating the set if it doesn't exist.

2. `audit.py`: An early attempt to compare Flickr set data with Lightroom publish collection dump.

3. `delete-orphans.py`: Identifies and optionally deletes orphaned photos that exist in the Lightroom publish collection but not in the managed Flickr set.

4. `fix-flickr.py`: Processes audit results to correct issues on the Flickr side, such as removing duplicate photos from sets.

5. `fix-lightroom.py`: Generates SQL updates to correct discrepancies in the Lightroom catalog based on audit results.

6. `flickr-ls.py`: Lists photos in a Flickr set or the entire Flickr account, outputting detailed photo information in JSONL format.

7. `lr-audit.py`: Audits and fixes Lightroom-Flickr set mismatches, capable of adding missing photos to the managed Flickr set.

8. `lr-check-duplicate-identifiers.py`: Scans the Lightroom catalog for photos with duplicate InstanceID or DocumentID values in their XMP metadata.

9. `lr-deep-audit.py`: Performs a timestamp-normalized deep audit for Lightroom-Flickr managed set synchronization, using precise capture times from XMP metadata.

10. `lr-deep-fix.py`: Processes results from `lr-deep-audit.py` to generate fix commands for mismatches, handling both timestamp and filename matches.

11. `lr-dump.py`: Extracts and compares Lightroom catalog data for specified images, outputting a flat comparison to a Markdown file.

12. `lr-flickr-audit-main.py`: The main script coordinating the audit process between the Lightroom catalog and Flickr set.

13. `lr-flickr-instanceid-report-yaml.py`: Generates a YAML report of InstanceIDs for Flickr-published photos from the Lightroom catalog.

14. `merge.py`: Addresses duplicate Flickr uploads by moving photos to a "To Be Deleted" set and updating the Lightroom catalog.

15. `swap.py`: Swaps Flickr photo references for two photos in the Lightroom catalog, useful for correcting mismatched uploads.

16. `unfluck.py`: A script designed to revert the mass of duplicate uploads from the Lightroom Flickr plugin malfunction.

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

These scripts were used in a specific sequence to address the duplicate upload issue:

1. Initial Assessment:
   ```
   python flickr-ls.py --all > all_photos.jsonl
   python lr-deep-audit.py
   ```
   This helped identify the extent of the duplicate uploads.

2. Fixing Duplicates:
   ```
   python lr-deep-fix.py
   python merge.py --keeper [keeper_id] --goner [goner_id] --force
   ```
   These steps were repeated as necessary to resolve duplicates.

3. Mass Cleanup:
   ```
   python unfluck.py 2023-01-01 --force --max-views 100
   ```
   This was used to revert the bulk of duplicate uploads from a specific date.

4. Audit V2:
   ```
   python lr-flickr-audit-main.py --full
   ```
   This was an improved rewrite of the initial `audit.py` script.

## Official Lightroom-Flickr plugin source code

The folder `lr-sdk-13.5` contains a copy of the source code of the official Lightroom-Flickr Plugin from Adobe, for quick reference and to help with troubleshooting.

The weird Adobe license allows me to distribute a copy of the code here, but to legally use it you need to download it from the Adobe site (it's part of the SDK download).

## Lightroom Data Extraction

The `audit.py` script requires a manual step to access the Lightroom catalog data:

1. Open the `.lrcat` file with DB Browser for SQLite.
2. Export the table `AgRemotePhoto`) as JSON.

Other scripts like `lr-dump.py` can extract data directly from the catalog file.

## Caution

These scripts were created for a one-time fix and can make significant changes to both the Lightroom catalog and Flickr account. If you need to use them:

1. Always back up your Lightroom catalog before running any scripts.
2. Use dry-run modes (usually by omitting the `--force` flag) to verify actions before applying changes.
3. Carefully review any generated SQL statements before executing them on your Lightroom catalog.
4. Be aware that these scripts have not been maintained or tested beyond their initial use.

## License

These scripts were developed by Generative AI and are not protected by copyright. No license is needed or possible.
