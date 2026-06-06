import boto3
import logging
import uuid
from app.config import settings

logger = logging.getLogger(__name__)

def upload_bytes_to_s3(content: bytes, content_type: str, key_prefix: str = "media/") -> str:
    """Upload bytes to S3 and return a presigned GET URL (expires in 1 hour).
    Requires AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY and S3_BUCKET in env.
    """
    bucket = settings.S3_BUCKET
    if not bucket:
        raise RuntimeError("S3_BUCKET not configured")
    session = boto3.session.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        region_name=settings.S3_REGION or None,
    )
    s3 = session.client('s3')
    key = f"{key_prefix}{uuid.uuid4().hex}.ogg"
    s3.put_object(Bucket=bucket, Key=key, Body=content, ContentType=content_type)
    url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)
    return url
