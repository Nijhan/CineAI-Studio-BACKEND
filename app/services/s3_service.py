import uuid
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

s3 = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)
BUCKET = settings.S3_BUCKET_NAME


def generate_upload_key(user_id: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1]
    return f"uploads/{user_id}/{uuid.uuid4()}.{ext}"


def get_public_url(key: str) -> str:
    return f"https://{BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def create_presigned_upload(key: str, content_type: str, expires: int = 3600) -> str:
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def create_presigned_download(key: str, expires: int = 3600) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": key},
        ExpiresIn=expires,
    )


def delete_object(key: str) -> None:
    try:
        s3.delete_object(Bucket=BUCKET, Key=key)
    except ClientError:
        pass
