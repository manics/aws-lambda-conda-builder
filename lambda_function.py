# https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-clients

import argparse
import boto3
from botocore.exceptions import ClientError
import os.path
import re
from subprocess import run
import sys
import yaml


# https://boto3.amazonaws.com/v1/documentation/api/1.16.53/guide/s3-uploading-files.html
def upload_file(filepath, bucket, key):
    """Upload a file to an S3 bucket

    :param filepath: File to upload
    :param bucket: Bucket to upload to
    :param key: S3 key
    """

    s3_client = boto3.client("s3")
    response = s3_client.upload_file(filepath, bucket, key)
    print(response)


def handler(event, context):
    print(f"{event=}")
    if "environment_yml" in event:
        environment_yml = event["environment_yml"]
        environment = yaml.safe_load(environment_yml)
    elif "environment" in event:
        environment = event["environment"]
    else:
        raise ValueError("No environment provided")

    try:
        s3bucket = event["s3bucket"]
    except KeyError:
        raise ValueError("No S3 bucket provided") from None

    try:
        s3prefix = event["s3prefix"]
    except KeyError:
        raise ValueError("No S3 prefix provided") from None

    if "name" not in environment:
        print("No name provided in environment, using 'custom-env'")
        environment["name"] = "custom-env"

    pack_found = False
    for package in environment["dependencies"]:
        if isinstance(package, dict):
            continue
        if re.match(r"conda-pack(\W|$)", package):
            pack_found = True
    if not pack_found:
        print("Adding conda-pack to environment")
        environment["dependencies"].append("conda-pack")

    print(f"Creating environment:\n{yaml.dump(environment)}")

    with open("environment.yml", "w") as f:
        f.write(yaml.dump(environment))

    name = environment["name"]
    run(["mamba", "env", "create", "-n", name, "--file", "environment.yml"], check=True)
    run(["conda", "pack", "-n", name, "-o", f"{name}.tar.gz"], check=True)

    source = f"{name}.tar.gz"
    destination = f"s3://{s3bucket}/{s3prefix}/{source}"
    print(f"Uploading {source} to {destination}")
    upload_file(source, s3bucket, s3prefix)
    return destination


def main():
    parser = argparse.ArgumentParser(description="Create a conda environment")
    parser.add_argument("environment", help="Conda environment file")
    parser.add_argument("--s3bucket", help="S3 bucket")
    parser.add_argument("--s3prefix", help="S3 prefix")
    args = parser.parse_args()
    environment_yml = open(args.environment).read()

    event = {
        "environment_yml": environment_yml,
        "s3bucket": args.s3bucket,
        "s3prefix": args.s3prefix,
    }
    r = handler(event, {})


if __name__ == "__main__":
    main()
