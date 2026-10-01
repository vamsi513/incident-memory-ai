from pathlib import PurePosixPath

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from core.config import settings
from core.exceptions import IngestionError
from ingestion.models import RawDocument


def load_markdown_files_from_s3(bucket: str, prefix: str = "") -> list[RawDocument]:
    client = boto3.client("s3", region_name=settings.aws_region)
    docs = []

    try:
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith(".md"):
                    continue

                response = client.get_object(Bucket=bucket, Key=key)
                content = response["Body"].read().decode("utf-8")
                stem = PurePosixPath(key).stem

                docs.append(
                    RawDocument(
                        doc_id=stem,
                        source="s3_markdown",
                        title=stem.replace("_", " ").title(),
                        content=content,
                        path=f"s3://{bucket}/{key}",
                        updated_at=obj["LastModified"].isoformat(),
                        metadata={"file_type": "md", "bucket": bucket, "key": key},
                    )
                )
    except (NoCredentialsError, PartialCredentialsError) as exc:
        raise IngestionError(f"AWS credentials not configured for S3: {exc}") from exc
    except ClientError as exc:
        raise IngestionError(f"S3 request failed: {exc}") from exc

    return docs
