"""
Provides logic for migrating job_script data from legacy db to nextgen db.
"""

import asyncio
import json

import aioboto3
from loguru import logger

from slurp.batch import batch
from slurp.config import settings


def migrate_job_scripts(nextgen_db, legacy_job_scripts, user_map, batch_size=1000):
    """
    Inserts job_script data to nextgen database.

    Given a list of legacy job_scripts, a user map, and an application map, create
    records in the nextgen database for each job_script.
    """
    logger.info("Migrating job_scripts to nextgen database")

    for job_script_batch in batch(legacy_job_scripts, batch_size):

        mogrified_params = ",".join(
            [
                nextgen_db.mogrify(
                    """
                    (
                        %(id)s,
                        %(name)s,
                        %(description)s,
                        %(owner_email)s,
                        %(application_id)s,
                        %(created)s,
                        %(updated)s
                    )
                    """,
                    dict(
                        id=job_script["id"],
                        name=job_script["job_script_name"],
                        description=job_script["job_script_description"],
                        owner_email=user_map[job_script["job_script_owner_id"]]["email"],
                        application_id=job_script["application_id"],
                        created=job_script["created_at"],
                        updated=job_script["updated_at"],
                    ),
                )
                for job_script in job_script_batch
            ]
        )

        nextgen_db.execute(
            """
            insert into job_scripts (
                id,
                job_script_name,
                job_script_description,
                job_script_owner_email,
                application_id,
                created_at,
                updated_at
            )
            values {}
            """.format(
                mogrified_params
            ),
        )

    logger.success("Finished migrating job_scripts")


async def transfer_job_script_files(legacy_job_scripts):

    logger.info("Start migrating job-script files to s3")

    main_filename = "application.sh"
    s3_key_template = f"job-scripts/{{job_script_id}}/main-file/{main_filename}"

    session = aioboto3.Session(
        aws_access_key_id=settings.NEXTGEN_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.NEXTGEN_AWS_SECRET_ACCESS_KEY,
    )

    async def transfer_helper(s3, job_script_data_as_string, job_script_id):

        try:
            unpacked_data = json.loads(job_script_data_as_string)
            job_script_content = unpacked_data.get(main_filename, "")
        except json.JSONDecodeError:
            logger.error(
                "Error loading job-script from json: ",
                job_script_data_as_string,
            )
            job_script_content = ""

        if not job_script_content:
            logger.warning(f"Empty job script content for {job_script_id=}")

        s3_key = s3_key_template.format(job_script_id=job_script_id)
        try:
            await s3.put_object(
                Body=job_script_content,
                Bucket=settings.NEXTGEN_S3_BUCKET_NAME,
                Key=s3_key,
            )
            return True
        except Exception:
            logger.error("Error uploading job-script to: ", s3_key)
            return False

    async with session.client("s3", endpoint_url=settings.NEXTGEN_S3_ENDPOINT_URL) as s3:

        tasks = (
            asyncio.create_task(
                transfer_helper(s3, job_script["job_script_data_as_string"], job_script["id"])
            )
            for job_script in legacy_job_scripts
        )

        result = await asyncio.gather(*tasks)

    logger.success(f"Finished migrating {len(result)} job-script files to s3")
