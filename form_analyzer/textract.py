import glob
import json
import logging
import os
import typing
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3


class AWSTextract:
    def __init__(self, aws_region_name: str = None,
                 aws_access_key_id: str = None,
                 aws_secret_access_key: str = None,
                 s3_bucket_name: str = None,
                 s3_folder: str = ''):
        self.aws_region_name = aws_region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.s3_bucket_name = s3_bucket_name
        self.s3_folder = s3_folder

    def query_aws(self, file_name: str):
        from form_analyzer import form_analyzer_logger

        if os.path.exists(f'{file_name}.json'):
            form_analyzer_logger.log(logging.DEBUG, f'Skipping {file_name}')
            return

        form_analyzer_logger.log(logging.INFO, f'Textracting {file_name}')

        if self.s3_bucket_name is not None:
            document = self.__upload_to_s3(file_name, self.s3_bucket_name, self.s3_folder)
        else:
            with open(file_name, "rb") as image_file:
                document = {
                    'Bytes': image_file.read(),
                }

        textract = boto3.client('textract', region_name=self.aws_region_name, aws_access_key_id=self.aws_access_key_id,
                                aws_secret_access_key=self.aws_secret_access_key)

        response = textract.analyze_document(
            Document=document,
            FeatureTypes=["FORMS"]
        )

        with open(f'{file_name}.json', 'w+') as f:
            json.dump(response, f)

    def __upload_to_s3(self, file_name: str,
                       s3_bucket_name: str = None,
                       s3_folder: str = '') -> typing.Dict:
        from form_analyzer import form_analyzer_logger

        s3 = boto3.client('s3', region_name=self.aws_region_name, aws_access_key_id=self.aws_access_key_id,
                          aws_secret_access_key=self.aws_secret_access_key)

        s3_file_name = s3_folder + os.path.split(file_name)[1]
        if 'Contents' not in s3.list_objects(Bucket=s3_bucket_name, Prefix=s3_file_name):
            form_analyzer_logger.log(logging.INFO, f'Uploading to S3 as {s3_file_name}')
            s3.upload_file(file_name, s3_bucket_name, s3_file_name)
        else:
            form_analyzer_logger.log(logging.DEBUG, f'File {s3_file_name} already on S3')

        return {
            'S3Object':
                {'Bucket': s3_bucket_name,
                 'Name': s3_file_name
                 }
        }


def run_textract(folder: str,
                 aws_region_name: str = None,
                 aws_access_key_id: str = None,
                 aws_secret_access_key: str = None,
                 s3_bucket_name: str = None,
                 s3_folder: str = ''):
    """
    Run AWS Textract on all PNG files in a folder.

    The function can either upload all files to an S3 bucket and process them from there or upload them directly to Textract. The analysis results are saved
    as JSON files. If a result JSON already exists for a PNG file, it will not be analyzed again.

    :param folder: PNG folder name
    :param aws_region_name: Optional AWS region name
    :param aws_access_key_id: Optional AWS access key ID
    :param aws_secret_access_key: Optional AWS secret access key
    :param s3_bucket_name: Optional S3 bucket name, if given, the function will upload the files to S3
    :param s3_folder: S3 bucket folder name, defaults to ''
    """
    with ThreadPoolExecutor(max_workers=4) as executor:
        textract = AWSTextract(aws_region_name, aws_access_key_id, aws_secret_access_key, s3_bucket_name, s3_folder)
        futures = []

        for file_name in sorted(glob.glob(f'{folder}/*.png')):
            futures.append(executor.submit(textract.query_aws, file_name))

        for future in as_completed(futures):
            future.result()
