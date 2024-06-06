# https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-clients

import argparse
import re
from subprocess import run  # nosec B404

import boto3
import yaml


def split_s3_url(s3url):
    bucket, key = s3url.lstrip("s3://").split("/", 1)
    return bucket, key


def upload_s3_file(filepath, bucket, key):
    s3 = boto3.client("s3")
    response = s3.upload_file(filepath, bucket, key)
    print(response)


def environment_yml_from_s3(s3url):
    s3 = boto3.client("s3")
    bucket, key = split_s3_url(s3url)
    obj = s3.get_object(Bucket=bucket, Key=key)
    y = yaml.safe_load(obj["Body"].read())
    return y


def handler(event, context):
    print(f"{event=}")

    if "environment_s3" in event:
        environment = environment_yml_from_s3(event["environment_s3"])
    elif "environment_string" in event:
        environment = yaml.safe_load(event["environment_string"])
    elif "environment" in event:
        environment = event["environment"]
    else:
        raise ValueError("No environment provided")

    upload_s3 = False
    if event.get("s3bucket") or event.get("s3prefix"):
        try:
            s3bucket = event["s3bucket"]
        except KeyError:
            raise ValueError("No S3 bucket provided") from None

        try:
            s3prefix = event["s3prefix"]
        except KeyError:
            raise ValueError("No S3 prefix provided") from None

        upload_s3 = True

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
    run(  # nosec B603, B607
        ["mamba", "env", "create", "-n", name, "--file", "environment.yml"], check=True
    )
    run(  # nosec B603, B607
        ["conda", "pack", "-n", name, "-o", f"{name}.tar.gz"], check=True
    )

    source = f"{name}.tar.gz"

    if upload_s3:
        destination = f"s3://{s3bucket}/{s3prefix}/{source}"
        print(f"Uploading to {destination}")
        upload_s3_file(source, s3bucket, s3prefix)
        return destination
    return source


def main():
    parser = argparse.ArgumentParser(description="Create a conda environment")
    parser.add_argument(
        "environment", help="Conda environment file, either a .yml file or an s3:// URL"
    )
    parser.add_argument("--s3bucket", help="Destination S3 bucket")
    parser.add_argument("--s3prefix", help="Destination S3 prefix")
    args = parser.parse_args()

    event = {
        "s3bucket": args.s3bucket,
        "s3prefix": args.s3prefix,
    }
    if args.environment.startswith("s3://"):
        event["environment_s3"] = args.environment
    else:
        with open(args.environment) as f:
            event["environment_string"] = f.read()
    _ = handler(event, {})


if __name__ == "__main__":
    main()
