import glob
import json
import logging
import os
import boto3


def run_textract(folder: str,
                 aws_region_name: str = None,
                 aws_access_key_id: str = None,
                 aws_secret_access_key: str = None,
                 use_s3: bool = False,
                 s3_bucket_name: str = None,
                 s3_folder: str = ''):
    from form_analyzer import form_analyzer_logger

    for file_name in sorted(glob.glob(f'{folder}/*.png')):
        if os.path.exists(f'{file_name}.json'):
            form_analyzer_logger.log(logging.DEBUG, f'Skipping {file_name}')
            continue

        form_analyzer_logger.log(logging.INFO, f'Textracting {file_name}')

        if use_s3:
            s3 = boto3.client('s3', region_name=aws_region_name, aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key)

            s3_file_name = s3_folder + os.path.split(file_name)[1]
            if 'Contents' not in s3.list_objects(Bucket=s3_bucket_name, Prefix=s3_file_name):
                form_analyzer_logger.log(logging.INFO, f'Uploading to S3 as {s3_file_name}')
                s3.upload_file(file_name, s3_bucket_name, s3_file_name)
            else:
                form_analyzer_logger.log(logging.DEBUG, f'File {s3_file_name} already on S3')

            document = {
                'S3Object':
                    {'Bucket': s3_bucket_name,
                     'Name': s3_file_name
                     }
            }

        else:
            with open(file_name, "rb") as image_file:
                document = {
                    'Bytes': image_file.read(),
                }

        textract = boto3.client('textract', region_name=aws_region_name, aws_access_key_id=aws_access_key_id,
                                aws_secret_access_key=aws_secret_access_key)

        response = textract.analyze_document(
            Document=document,
            FeatureTypes=["FORMS"]
        )

        with open(f'{file_name}.json', 'w+') as f:
            json.dump(response, f)
