"""
s3_storage.py
AWS S3 operations — upload, signed URL generation.
Mirrors the Aeternum files table / S3 storage pattern.
"""

import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION            = os.getenv("AWS_REGION", "us-east-2")
S3_BUCKET             = os.getenv("S3_BUCKET", "memoria-media")


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def upload_file(local_path: str, s3_path: str) -> bool:
    """
    Uploads a local file to S3.
    s3_path: e.g. "memories/rose/apple-pie.jpg"
    """
    client = get_s3_client()
    try:
        client.upload_file(local_path, S3_BUCKET, s3_path)
        print(f"✅ Uploaded {local_path} → s3://{S3_BUCKET}/{s3_path}")
        return True
    except ClientError as e:
        print(f"❌ Upload failed: {e}")
        return False


def upload_from_url(image_url: str, s3_path: str) -> bool:
    """
    Downloads an image from a URL and uploads it to S3.
    Used to seed placeholder images from Unsplash into real S3.
    """
    import urllib.request
    import tempfile

    client = get_s3_client()
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            urllib.request.urlretrieve(image_url, tmp.name)
            client.upload_file(
                tmp.name,
                S3_BUCKET,
                s3_path,
                ExtraArgs={"ContentType": "image/jpeg"},
            )
        os.unlink(tmp.name)
        print(f"✅ Seeded {s3_path} into S3")
        return True
    except Exception as e:
        print(f"❌ Failed to seed {s3_path}: {e}")
        return False


def get_signed_url(s3_path: str, expires_in: int = 3600) -> str:
    """
    Generates a pre-signed URL for an S3 object.
    expires_in: seconds until expiry (default 1 hour)
    """
    client = get_s3_client()
    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_path},
            ExpiresIn=expires_in,
        )
        return url
    except ClientError as e:
        print(f"❌ Could not generate signed URL: {e}")
        return ""


def file_exists(s3_path: str) -> bool:
    """Check if a file exists in S3."""
    client = get_s3_client()
    try:
        client.head_object(Bucket=S3_BUCKET, Key=s3_path)
        return True
    except ClientError:
        return False
