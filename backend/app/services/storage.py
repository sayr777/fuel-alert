import hashlib
import uuid

import boto3
from botocore.client import Config

from app.config import get_settings

settings = get_settings()

_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version="s3v4"),
            use_ssl=settings.s3_use_ssl,
        )
    return _s3_client


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def upload_photo(data: bytes, content_type: str = "image/jpeg") -> str:
    """Uploads photo bytes to the bucket and returns the s3_key."""
    key = f"reports/{uuid.uuid4().hex}.jpg"
    client = get_s3_client()
    client.put_object(Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=content_type)
    return key


def public_url(s3_key: str) -> str:
    return f"{settings.s3_public_url}/{s3_key}"
