import os
import time

import boto3


def process(input):
    time.sleep(30)
    return "blah"


def main():
    region_name = os.environ['REGION_NAME']
    input_bucket = os.environ['INPUT_BUCKET_NAME']
    input_object = os.environ['INPUT_OBJECT_NAME']
    output_bucket = os.environ['OUTPUT_BUCKET_NAME']
    output_object = os.environ.get('OUTPUT_BUCKET_OBJECT', input_object)

    s3_client = boto3.client('s3', region_name=region_name)
    obj = s3_client.get_object(Bucket=input_bucket, Key=input_object)
    data = obj['Body'].read()
    output = process(data)
    if not isinstance(output, bytes):
        output = bytes(output, 'utf8')
    s3_client.put_object(Body=output, Bucket=output_bucket, Key=output_object)


if __name__ == "__main__":
    main()
