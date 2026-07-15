import boto3

from polibot.config import get_settings


def get_rustfs_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.rustfs_endpoint,
        aws_access_key_id=settings.rustfs_access_key,
        aws_secret_access_key=settings.rustfs_secret_key,
    )


def upload_file(local_path: str, key: str, bucket: str | None = None) -> str:
    settings = get_settings()
    bucket = bucket or settings.rustfs_bucket
    client = get_rustfs_client()
    client.upload_file(local_path, bucket, key)
    return key


def get_presigned_url(key: str, bucket: str | None = None, expires_in: int = 3600) -> str:
    settings = get_settings()
    bucket = bucket or settings.rustfs_bucket
    client = get_rustfs_client()
    return client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires_in
    )
