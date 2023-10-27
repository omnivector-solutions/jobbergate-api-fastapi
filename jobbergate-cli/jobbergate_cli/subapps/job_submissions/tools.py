"""
Provide tool functions for working with Job Submission data
"""

import os
import re
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Optional, cast

from loguru import logger

from jobbergate_cli.config import settings
from jobbergate_cli.exceptions import Abort
from jobbergate_cli.requests import make_request
from jobbergate_cli.schemas import JobbergateContext, JobSubmissionCreateRequestData, JobSubmissionResponse
from jobbergate_cli.subapps.job_scripts.tools import download_job_script_files, validate_parameter_file


SBATCH_PATH = os.environ.get("SBATCH_PATH", "/usr/bin/sbatch")


def jobbergate_run(filename, *argv):
    """Execute Job Submission."""
    cmd = [SBATCH_PATH, filename]
    for arg in argv:
        cmd.append(arg)
    logger.debug(f"Executing: {''.join(cmd)}")
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate(b"sbatch output")

    rc = p.returncode

    return output.decode("utf-8"), err.decode("utf-8"), rc


def create_job_submission(
    jg_ctx: JobbergateContext,
    job_script_id: int,
    name: str,
    description: Optional[str] = None,
    cluster_name: Optional[str] = None,
    execution_directory: Optional[Path] = None,
    execution_parameters_file: Optional[Path] = None,
) -> JobSubmissionResponse:
    """
    Create a Job Submission from the given Job Script.

    :param: jg_ctx:                    The JobbergateContext. Used to retrieve the client for requests
                                       and the email of the submitting user
    :param: job_script_id:             The ``id`` of the Job Script to submit to Slurm
    :param: name:                      The name to attach to the Job Submission
    :param: description:               An optional description that may be added to the Job Submission
    :param: cluster_name:              An optional cluster_name for the cluster where the job should be executed,
                                       If left off, it will default to the DEFAULT_CLUSTER_NAME from the settings.
                                       If no default is set, an exception will be raised.
    :param: execution_directory:       An optional directory where the job should be executed. If provided as a
                                       relative path, it will be constructed as an absolute path relative to
                                       the current working directory.
    :param: execution_parameters_file: An optional file containing the execution parameters for the job.

    :returns: The Job Submission data returned by the API after creating the new Job Submission
    """

    # Make static type checkers happy
    assert jg_ctx.client is not None, "jg_ctx.client is uninitialized"
    assert jg_ctx.persona is not None, "jg_ctx.persona is uninitialized"

    if cluster_name is None:
        cluster_name = settings.DEFAULT_CLUSTER_NAME

    Abort.require_condition(
        cluster_name is not None,
        "No cluster name supplied and no default exists. Cannot submit to an unknown cluster!",
        raise_kwargs=dict(
            subject="No cluster Name",
            support=True,
        ),
    )

    if execution_directory is None:
        execution_directory = Path.cwd()

    files = download_job_script_files(job_script_id, jg_ctx)
    output, err, rc = jobbergate_run(files.pop().as_posix(), name)

    logger.debug(f"Job submission output: {output}")
    logger.debug(f"Job submission error: {err}")
    logger.debug(f"Job submission return code: {rc}")

    Abort.require_condition(
        rc == 0,
        f"Failed to execute submission with error: {err}",
        raise_kwargs=dict(
            subject="sbatch error",
            support=False,
        ),
    )

    match = re.search(r"^Submitted batch job (\d+)", output)
    slurm_job_id = int(match.group(1)) if match else None

    job_submission_data = JobSubmissionCreateRequestData(
        name=name,
        description=description,
        job_script_id=job_script_id,
        cluster_name="sbatch-from-cli",
        execution_directory=execution_directory.resolve(),
    )

    if execution_parameters_file is not None:
        job_submission_data.execution_parameters = validate_parameter_file(execution_parameters_file)

    result = cast(
        JobSubmissionResponse,
        make_request(
            jg_ctx.client,
            "/jobbergate/job-submissions",
            "POST",
            expected_status=201,
            abort_message="Couldn't create job submission",
            support=True,
            request_model=job_submission_data,
            response_model_cls=JobSubmissionResponse,
        ),
    )

    result.slurm_job_id = slurm_job_id
    return result


def fetch_job_submission_data(
    jg_ctx: JobbergateContext,
    job_submission_id: int,
) -> JobSubmissionResponse:
    """
    Retrieve a job submission from the API by ``id``
    """
    # Make static type checkers happy
    assert jg_ctx.client is not None, "Client is uninitialized"

    return cast(
        JobSubmissionResponse,
        make_request(
            jg_ctx.client,
            f"/jobbergate/job-submissions/{job_submission_id}",
            "GET",
            expected_status=200,
            abort_message=f"Couldn't retrieve job submission {job_submission_id} from API",
            support=True,
            response_model_cls=JobSubmissionResponse,
        ),
    )
