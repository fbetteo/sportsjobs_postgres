
import boto3
from botocore.client import Config

import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('sportsjobs_postgres') / '.env' 
load_dotenv(dotenv_path=env_path)
# R2 credentials
CLOUDFLARE_R2_ACCESS_KEY =os.getenv("CLOUDFLARE_R2_ACCESS_KEY")
CLOUDFLARE_R2_SECRET_KEY = os.getenv("CLOUDFLARE_R2_SECRET_KEY")
CLOUDFLARE_R2_BUCKET_NAME = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
CLOUDFLARE_R2_ENDPOINT_URL = os.getenv("CLOUDFLARE_R2_ENDPOINT_URL")

# Initialize S3 client with R2 settings
s3_client = boto3.client(
    's3',
    endpoint_url=CLOUDFLARE_R2_ENDPOINT_URL,
    aws_access_key_id=CLOUDFLARE_R2_ACCESS_KEY,
    aws_secret_access_key=CLOUDFLARE_R2_SECRET_KEY,
    config=Config(signature_version='s3v4'),
)

# Upload an image
def upload_image(file_path, key_name):
    """
    Uploads an image to the R2 bucket.
    
    :param file_path: Path to the local image file.
    :param key_name: The key (file name) to use in the R2 bucket.
    """
    try:
        with open(file_path, "rb") as f:
            s3_client.upload_fileobj(f, CLOUDFLARE_R2_BUCKET_NAME, key_name)
        print(f"Uploaded {file_path} to {CLOUDFLARE_R2_BUCKET_NAME}/{key_name}")
    except Exception as e:
        print(f"Failed to upload {file_path}: {e}")

# Example usage
IMAGE_PATH = "database/blogposts/images"
for img in os.listdir(f"{IMAGE_PATH}"):
    upload_image(f"{IMAGE_PATH}/{img}", f"blogposts/images/{img}")
