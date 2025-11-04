"""
MinIO
CPG2PVG-AI System MinIO Setup
"""

import asyncio
import os
import sys
from pathlib import Path

# Python
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.file_storage import minio_client
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


async def setup_minio():
    """MinIO"""
    try:
        settings = get_settings()
        logger.info("MinIO...")

        # bucket
        client = await minio_client._get_client()

        logger.info(f"MinIO")
        logger.info(f"Endpoint: {settings.MINIO_ENDPOINT}")
        logger.info(f"Bucket: {settings.MINIO_BUCKET_NAME}")
        logger.info(f"Region: {settings.MINIO_REGION}")
        logger.info(f"Secure: {settings.MINIO_SECURE}")

        # 
        logger.info("...")
        test_content = b"MinIO - CPG2PVG-AI System"
        test_filename = "test_minio_connection.txt"

        # 
        upload_result = await minio_client.upload_file(
            file_content=test_content,
            original_filename=test_filename,
            prefix="tests",
            metadata={"test": "connection_test"}
        )
        logger.info(f": {upload_result['object_name']}")

        # 
        downloaded_content = await minio_client.download_file(upload_result['object_name'])
        if downloaded_content == test_content:
            logger.info("")
        else:
            logger.error("")

        # 
        file_info = await minio_client.get_file_info(upload_result['object_name'])
        logger.info(f": {file_info}")

        # URL
        presigned_url = await minio_client.generate_presigned_url(upload_result['object_name'])
        logger.info(f"URL (1)")

        # 
        await minio_client.delete_file(upload_result['object_name'])
        logger.info("")

        logger.info("MinIO")
        return True

    except Exception as e:
        logger.error(f"MinIO: {e}")
        return False


async def check_minio_health():
    """MinIO"""
    try:
        logger.info("MinIO...")

        client = await minio_client._get_client()

        # 
        loop = asyncio.get_event_loop()

        def health_check():
            try:
                # bucket
                buckets = list(client.list_buckets())
                return True, [bucket.name for bucket in buckets]
            except Exception as e:
                return False, str(e)

        is_healthy, result = await loop.run_in_executor(None, health_check)

        if is_healthy:
            logger.info(f"MinIObuckets: {result}")
        else:
            logger.error(f"MinIO: {result}")

        return is_healthy

    except Exception as e:
        logger.error(f"MinIO: {e}")
        return False


async def create_minio_directories():
    """MinIO"""
    try:
        logger.info("MinIO...")

        # 
        directories = [
            "guidelines/",
            "documents/",
            "uploads/",
            "exports/",
            "temp/",
            "tests/",
            "backups/",
            "guidelines/original/",
            "guidelines/processed/",
            "documents/patient_versions/",
            "documents/clinical_versions/",
            "exports/reports/",
            "exports/summaries/",
            "temp/processing/",
            "temp/uploads/",
            "backups/database/",
            "backups/files/"
        ]

        created_count = 0
        for directory in directories:
            try:
                # 
                empty_content = b""
                await minio_client.upload_file(
                    file_content=empty_content,
                    original_filename=".keep",
                    prefix=directory.rstrip("/"),
                    metadata={"directory": "true", "auto_created": "true"}
                )
                created_count += 1
                logger.info(f": {directory}")

            except Exception as e:
                logger.warning(f" {directory}: {e}")

        logger.info(f"MinIO {created_count} ")
        return True

    except Exception as e:
        logger.error(f"MinIO: {e}")
        return False


async def setup_minio_policies():
    """MinIO"""
    try:
        logger.info("MinIO...")

        settings = get_settings()
        client = await minio_client._get_client()

        # 
        loop = asyncio.get_event_loop()

        def set_policy():
            try:
                # bucket
                if settings.is_development():
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": "*"},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{settings.MINIO_BUCKET_NAME}/*"]
                            }
                        ]
                    }

                    import json
                    client.set_bucket_policy(
                        bucket_name=settings.MINIO_BUCKET_NAME,
                        policy=json.dumps(policy)
                    )
                    logger.info("")
                else:
                    logger.info("")

            except Exception as e:
                logger.warning(f": {e}")

        await loop.run_in_executor(None, set_policy)
        logger.info("MinIO")
        return True

    except Exception as e:
        logger.error(f"MinIO: {e}")
        return False


async def main():
    """"""
    print(" MinIO")
    print("=" * 50)

    # 
    settings = get_settings()
    print(f"MinIO Endpoint: {settings.MINIO_ENDPOINT}")
    print(f"MinIO Access Key: {settings.MINIO_ACCESS_KEY[:10]}...")
    print(f"MinIO Bucket: {settings.MINIO_BUCKET_NAME}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print()

    # 
    print("1. MinIO...")
    is_healthy = await check_minio_health()
    if not is_healthy:
        print("[FAIL] MinIO")
        return False
    print("[OK] MinIO")
    print()

    # 
    print("2. MinIO...")
    setup_success = await setup_minio()
    if not setup_success:
        print("[FAIL] MinIO")
        return False
    print("[OK] MinIO")
    print()

    # 
    print("3. ...")
    dirs_created = await create_minio_directories()
    if dirs_created:
        print("[OK] ")
    else:
        print("[WARN] ")
    print()

    # 
    print("4. ...")
    policies_set = await setup_minio_policies()
    if policies_set:
        print("[OK] ")
    else:
        print("[WARN] ")
    print()

    print("[SUCCESS] MinIO")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)