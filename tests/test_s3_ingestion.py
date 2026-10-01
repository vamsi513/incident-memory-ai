"""
Tests for ingestion/connectors/s3_files.py and the ingestion_source wiring
in ingestion/pipeline.py.

S3 calls are stubbed with botocore.stub.Stubber (ships with boto3, no extra
test dependency) rather than hitting real AWS -- unlike the Bedrock judge
test, there's no real-call content to verify here, just that the connector
shapes its requests and parses responses correctly.
"""

from datetime import datetime, timezone

import boto3
import pytest
from botocore.stub import Stubber

from core.exceptions import IngestionError
from ingestion.connectors.s3_files import load_markdown_files_from_s3


def test_loads_markdown_objects_and_skips_others():
    client = boto3.client("s3", region_name="us-east-1")
    stubber = Stubber(client)

    stubber.add_response(
        "list_objects_v2",
        {
            "Contents": [
                {
                    "Key": "runbooks/auth_outage.md",
                    "LastModified": datetime(2026, 1, 1, tzinfo=timezone.utc),
                },
                {
                    "Key": "runbooks/diagram.png",
                    "LastModified": datetime(2026, 1, 1, tzinfo=timezone.utc),
                },
            ]
        },
        {"Bucket": "incident-docs", "Prefix": "runbooks/"},
    )
    stubber.add_response(
        "get_object",
        {"Body": _body(b"# Auth Outage\n\nRotate the cert.")},
        {"Bucket": "incident-docs", "Key": "runbooks/auth_outage.md"},
    )

    with stubber:
        docs = _load(client, "incident-docs", "runbooks/")

    assert len(docs) == 1
    doc = docs[0]
    assert doc.doc_id == "auth_outage"
    assert doc.title == "Auth Outage"
    assert doc.content == "# Auth Outage\n\nRotate the cert."
    assert doc.path == "s3://incident-docs/runbooks/auth_outage.md"
    assert doc.source == "s3_markdown"


def test_wraps_client_errors_as_ingestion_error():
    client = boto3.client("s3", region_name="us-east-1")
    stubber = Stubber(client)
    stubber.add_client_error("list_objects_v2", service_error_code="NoSuchBucket")

    with stubber, pytest.raises(IngestionError):
        _load(client, "does-not-exist")


def _load(client, bucket, prefix=""):
    original_client_factory = boto3.client
    boto3.client = lambda *a, **kw: client
    try:
        return load_markdown_files_from_s3(bucket, prefix)
    finally:
        boto3.client = original_client_factory


def _body(data: bytes):
    import io

    from botocore.response import StreamingBody

    return StreamingBody(io.BytesIO(data), len(data))
