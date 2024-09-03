# fix-lightroom.py:
# This script processes the missing photos from the audit.py results and generates SQL updates to fix Lightroom.
# The script takes a path to an audit results JSON file as a command-line argument.
# For each photo in the "missing_in_lightroom" section of the audit results, the script checks if the photo has any favorites or comments.
# If the photo has favorites or comments, it is skipped.
# If the photo has a matching photo (based on timestamp) in Lightroom, SQL update statements are generated to replace the unwanted photo's ID with the golden photo's ID.
# The SQL updates are written to a file named "lightroom_updates.sql".

import json
import sys

def generate_sql_update(golden_id, unwanted_id):
    """
    Generate SQL update statement for AgRemotePhoto using SQL REPLACE function.

    Use case example:
    golden_id: '53949265761' (the ID missing in Lightroom, which we want to keep)
    unwanted_id: '14097127335' (the ID in Lightroom that we want to replace)

    The resulting SQL should:
    1. Find the record with remoteId '14097127335'
    2. Change its remoteId to '53949265761'
    3. In its url, replace '/14097127335/' with '/53949265761/'
    """
    return f"UPDATE AgRemotePhoto SET remoteId = '{golden_id}', url = REPLACE(url, '/{unwanted_id}/', '/{golden_id}/') WHERE remoteId = '{unwanted_id}';"

def process_lightroom_updates(audit_results):
    """
    Process the missing photos from the audit results and generate SQL updates.

    For each photo in "missing_in_lightroom":
    - The photo itself is the golden record (the one missing in Lightroom, which we want to keep)
    - The matching photo is the unwanted one (the one in Lightroom that we want to replace)
    """
    sql_updates = []

    for photo in audit_results["missing_in_lightroom"]:
        if int(photo["favorites"]) > 0 or int(photo["comments"]) > 0:
            print(f"Skipping photo {photo['photo_id']} due to favorites or comments")
            continue
        if photo["matching"]:
            # 'photo' is the golden photo (missing in Lightroom, which we want to keep)
            golden_photo = photo
            # 'photo["matching"][0]' is the unwanted photo (in Lightroom, which we want to replace)
            unwanted_photo = photo["matching"][0]

            # Generate SQL to replace unwanted_photo's ID with golden_photo's ID
            sql_update = generate_sql_update(golden_photo["photo_id"], unwanted_photo["photo_id"])
            sql_updates.append(sql_update)
            print(f"Generated SQL update: Replace {unwanted_photo['photo_id']} with {golden_photo['photo_id']}")

    return sql_updates

def main():
    if len(sys.argv) != 2:
        print("Usage: python fix-lightroom.py <path_to_audit_results.json>")
        sys.exit(1)

    audit_results_path = sys.argv[1]

    # Load audit results
    with open(audit_results_path, 'r') as f:
        audit_results = json.load(f)

    # Process the missing photos and generate SQL updates
    sql_updates = process_lightroom_updates(audit_results)

    # Write SQL updates to a file
    if sql_updates:
        with open("lightroom_updates.sql", "w") as f:
            f.write("\n".join(sql_updates))
        print("SQL updates written to lightroom_updates.sql")
    else:
        print("No SQL updates generated.")

if __name__ == "__main__":
    main()

"""
Example use case:

Suppose the audit_results.json contains:

{
  "missing_in_lightroom": [
    {
      "photo_id": "53949265761",
      "title": "'California' (E-M1, OLYMPUS M.12-40mm F2.8, ISO 200 1-1600 sec at f - 5.6, 24 mm-e, 2014-04-13).jpg",
      "date_taken": "2014-04-13 13:33:40",
      "date_upload": "2024-08-26T08:14:52",
      "views": "8",
      "favorites": 0,
      "comments": "0",
      "matching": [
        {
          "photo_id": "14097127335",
          "title": "'California' - E-M1, OLYMPUS M.12-40mm F2.8, ISO 200 1-1600 sec at f - 5.6, 24 mm, 2014-04-13 13.33.40.jpg",
          "date_taken": "2014-04-13 13:33:40",
          "date_upload": "2024-08-25T14:16:20",
          "views": "175",
          "favorites": 0,
          "comments": "0"
        }
      ]
    }
  ]
}

The script will generate this SQL:

UPDATE AgRemotePhoto SET remoteId = '53949265761', url = REPLACE(url, '/14097127335/', '/53949265761/') WHERE remoteId = '14097127335';

This SQL will:
1. Find the record in AgRemotePhoto where remoteId is '14097127335' (the unwanted ID in Lightroom)
2. Change that remoteId to '53949265761' (the golden ID missing from Lightroom)
3. In the url field of that record, replace '/14097127335/' with '/53949265761/'

The end result is that the database will now refer to the golden photo (53949265761) instead of the unwanted one (14097127335).
"""