import argparse
import fnmatch
import os

import boto3


def search_s3_objects(bucket_name, search_keyword):
    s3_client = boto3.client("s3")
    search_results = []

    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            if fnmatch.fnmatch(obj["Key"], search_keyword):
                search_results.append(obj["Key"])

    return search_results


def main(args):
    results = search_s3_objects(args.bucket_name, args.search_keyword)

    if results:
        print(f"Found {len(results)} objects containing '{args.search_keyword}':")
        for obj in results:
            print(obj)
    else:
        print(f"No objects found containing '{args.search_keyword}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search objects in an S3 bucket that match a specified keyword.",
        epilog='aws-vault exec nilebank-stg-admin -- python3 main.py nilebank-stg-s3-datalake "*.tif"',
    )
    parser.add_argument(
        "bucket_name",
        help="Name of the S3 bucket to search.Like nilebank-proto-s3-datalake",
    )
    parser.add_argument("search_keyword", help="Keyword to search for in the bucket.")

    args = parser.parse_args()
    main(args)
