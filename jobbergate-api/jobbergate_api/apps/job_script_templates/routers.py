"""Router for the Job Script Template resource."""

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, HTTPException, Path, Query
from fastapi import Response as FastAPIResponse
from fastapi import UploadFile, status
from fastapi.responses import StreamingResponse
from fastapi_pagination import Page
from loguru import logger
from sqlalchemy.exc import IntegrityError

from jobbergate_api.apps.constants import FileType
from jobbergate_api.apps.dependecies import file_services, s3_bucket, secure_services
from jobbergate_api.apps.garbage_collector import garbage_collect
from jobbergate_api.apps.job_script_templates.constants import WORKFLOW_FILE_NAME
from jobbergate_api.apps.job_script_templates.models import JobScriptTemplateFile, WorkflowFile
from jobbergate_api.apps.job_script_templates.schemas import (
    JobTemplateCreateRequest,
    JobTemplateDetailedView,
    JobTemplateListView,
    JobTemplateUpdateRequest,
    RunTimeConfig,
    TemplateFileDetailedView,
    WorkflowFileDetailedView,
)
from jobbergate_api.apps.job_script_templates.services import (
    crud_service,
    template_file_service,
    workflow_file_service,
)
from jobbergate_api.apps.permissions import Permissions
from jobbergate_api.apps.schemas import ListParams
from jobbergate_api.storage import SecureSession, secure_session

router = APIRouter(prefix="/job-script-templates", tags=["Job Script Templates"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=JobTemplateDetailedView,
    description="Endpoint for job script template creation",
)
async def job_script_template_create(
    create_request: JobTemplateCreateRequest,
    secure_session: SecureSession = Depends(
        secure_services(Permissions.JOB_TEMPLATES_EDIT, services=[crud_service])
    ),
):
    """Create a new job script template."""
    logger.info(f"Creating a new job script template with {create_request=}")

    if secure_session.identity_payload.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The token payload does not contain an email",
        )

    try:
        new_job_template = await crud_service.create(
            owner_email=secure_session.identity_payload.email,
            **create_request.dict(exclude_unset=True),
        )
    except IntegrityError:
        message = f"Job script template with the {create_request.identifier=} already exists"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)

    return new_job_template


@router.get(
    "/{id_or_identifier}",
    description="Endpoint to return a job script template by its id or identifier",
    response_model=JobTemplateDetailedView,
    dependencies=[Depends(secure_services(Permissions.JOB_TEMPLATES_VIEW, services=[crud_service]))],
)
async def job_script_template_get(id_or_identifier: int | str = Path()):
    """Get a job script template by id or identifier."""
    logger.info(f"Getting job script template with {id_or_identifier=}")
    return await crud_service.get(id_or_identifier, include_files=True)


@router.get(
    "",
    description="Endpoint to return a list of job script templates",
    response_model=Page[JobTemplateListView],
)
async def job_script_template_get_list(
    list_params: ListParams = Depends(),
    include_null_identifier: bool = Query(False),
    secure_session: SecureSession = Depends(
        secure_services(Permissions.JOB_TEMPLATES_VIEW, services=[crud_service])
    ),
):
    """Get a list of job script templates."""
    logger.debug("Preparing to list job script templates")

    list_kwargs = list_params.dict(exclude_unset=True, exclude={"user_only", "include_parent"})

    if list_params.user_only:
        list_kwargs["owner_email"] = secure_session.identity_payload.email

    return await crud_service.paginated_list(
        **list_kwargs,
        include_null_identifier=include_null_identifier,
    )


@router.put(
    "/{id_or_identifier}",
    status_code=status.HTTP_200_OK,
    description="Endpoint to update a job script template by id or identifier",
    response_model=JobTemplateDetailedView,
)
async def job_script_template_update(
    update_request: JobTemplateUpdateRequest,
    id_or_identifier: int | str = Path(),
    secure_session: SecureSession = Depends(
        secure_services(Permissions.JOB_TEMPLATES_EDIT, services=[crud_service], ensure_email=True)
    ),
):
    """Update a job script template by id or identifier."""
    logger.info(f"Updating job script template {id_or_identifier=} with {update_request=}")
    async with crud_service.ensure_attribute(
        id_or_identifier,
        owner_email=secure_session.identity_payload.email,
    ) as s:
        return await s.update(id_or_identifier, **update_request.dict(exclude_unset=True))


@router.delete(
    "/{id_or_identifier}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Endpoint to delete a job script template by id or identifier",
)
async def job_script_template_delete(
    id_or_identifier: int | str = Path(),
    secure_session: SecureSession = Depends(
        secure_services(Permissions.JOB_TEMPLATES_EDIT, services=[crud_service], ensure_email=True)
    ),
):
    """Delete a job script template by id or identifier."""
    logger.info(f"Deleting job script template with {id_or_identifier=}")
    async with crud_service.ensure_attribute(
        id_or_identifier,
        owner_email=secure_session.identity_payload.email,
    ) as s:
        await s.delete(id_or_identifier)
    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{id_or_identifier}/upload/template/{file_name:path}",
    description="Endpoint to get a file from a job script template by id or identifier",
    dependencies=[
        Depends(
            secure_services(Permissions.JOB_TEMPLATES_VIEW, services=[crud_service, template_file_service])
        ),
        Depends(file_services(template_file_service)),
    ],
)
async def job_script_template_get_file(
    id_or_identifier: int | str = Path(),
    file_name: str = Path(),
):
    """
    Get a job script template file by id or identifier.

    Note:
        See https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
    """
    logger.debug(f"Getting template file {file_name=} from job script template {id_or_identifier=}")
    job_script_template = await crud_service.get(id_or_identifier)
    job_script_template_file = await template_file_service.get(job_script_template.id, file_name)
    return StreamingResponse(
        content=await template_file_service.stream_file_content(job_script_template_file),
        media_type="text/plain",
        headers={"filename": job_script_template_file.filename},
    )


@router.put(
    "/{id_or_identifier}/upload/template/{file_type}",
    status_code=status.HTTP_200_OK,
    description="Endpoint to upload a file to a job script template by id or identifier",
    response_model=TemplateFileDetailedView,
    dependencies=[Depends(file_services(template_file_service))],
)
async def job_script_template_upload_file(
    id_or_identifier: int | str = Path(),
    file_type: FileType = Path(),
    upload_file: UploadFile = File(..., description="File to upload"),
    secure_session: SecureSession = Depends(
        secure_services(
            Permissions.JOB_TEMPLATES_EDIT, services=[crud_service, template_file_service], ensure_email=True
        )
    ),
):
    """Upload a file to a job script template by id or identifier."""
    if upload_file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The upload file has no filename",
        )

    logger.debug(f"Uploading file {upload_file.filename} to job script template {id_or_identifier=}")

    async with crud_service.ensure_attribute(
        id_or_identifier,
        owner_email=secure_session.identity_payload.email,
    ) as s:
        job_script_template = await s.get(id_or_identifier)

    return await template_file_service.upsert(
        parent_id=job_script_template.id,
        filename=upload_file.filename,
        upload_content=upload_file,
        file_type=file_type,
    )


@router.delete(
    "/{id_or_identifier}/upload/template/{file_name:path}",
    status_code=status.HTTP_200_OK,
    description="Endpoint to delete a file to a job script template by id or identifier",
    dependencies=[Depends(file_services(template_file_service))],
)
async def job_script_template_delete_file(
    id_or_identifier: int | str = Path(),
    file_name: str = Path(),
    secure_session: SecureSession = Depends(
        secure_services(
            Permissions.JOB_TEMPLATES_EDIT, services=[crud_service, template_file_service], ensure_email=True
        )
    ),
):
    """Delete a file from a job script template by id or identifier."""
    async with crud_service.ensure_attribute(
        id_or_identifier,
        owner_email=secure_session.identity_payload.email,
    ) as s:
        job_script_template = await s.get(id_or_identifier)

    job_script_template_file = await template_file_service.get(job_script_template.id, file_name)
    await template_file_service.delete(job_script_template_file)


@router.get(
    "/{id_or_identifier}/upload/workflow",
    description="Endpoint to get a workflow file from a job script template by id or identifier",
    dependencies=[
        Depends(
            secure_services(Permissions.JOB_TEMPLATES_VIEW, services=[crud_service, workflow_file_service])
        ),
        Depends(file_services(workflow_file_service)),
    ],
)
async def job_script_workflow_get_file(id_or_identifier: int | str = Path()):
    """
    Get a workflow file by id or identifier.

    Note:
        See https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
    """
    logger.debug(f"Getting workflow file from job script template {id_or_identifier=}")
    job_script_template = await crud_service.get(id_or_identifier)
    workflow_file = await workflow_file_service.get(job_script_template.id, WORKFLOW_FILE_NAME)
    return StreamingResponse(
        content=await workflow_file_service.stream_file_content(workflow_file),
        media_type="text/plain",
        headers={"filename": WORKFLOW_FILE_NAME},
    )


@router.put(
    "/{id_or_identifier}/upload/workflow",
    status_code=status.HTTP_200_OK,
    description="Endpoint to upload a file to a job script template by id or identifier",
    response_model=WorkflowFileDetailedView,
    dependencies=[Depends(file_services(workflow_file_service))],
)
async def job_script_workflow_upload_file(
    id_or_identifier: int | str = Path(),
    runtime_config: RunTimeConfig = Body(),
    upload_file: UploadFile = File(..., description="File to upload"),
    secure_session: SecureSession = Depends(
        secure_services(
            Permissions.JOB_TEMPLATES_EDIT, services=[crud_service, workflow_file_service], ensure_email=True
        )
    ),
):
    """Upload a file to a job script workflow by id or identifier."""
    logger.debug(f"Uploading workflow file to job script template {id_or_identifier=}: {runtime_config}")
    async with crud_service.ensure_attribute(
        id_or_identifier,
        owner_email=secure_session.identity_payload.email,
    ) as s:
        job_script_template = await s.get(id_or_identifier)

    return await workflow_file_service.upsert(
        parent_id=job_script_template.id,
        filename=WORKFLOW_FILE_NAME,
        upload_content=upload_file,
        runtime_config=runtime_config.dict(),
    )


@router.delete(
    "/{id_or_identifier}/upload/workflow",
    status_code=status.HTTP_200_OK,
    description="Endpoint to delete a workflow file from a job script template by id or identifier",
    dependencies=[Depends(file_services(workflow_file_service))],
)
async def job_script_workflow_delete_file(
    id_or_identifier: int | str = Path(),
    secure_session: SecureSession = Depends(
        secure_services(
            Permissions.JOB_TEMPLATES_EDIT, services=[crud_service, workflow_file_service], ensure_email=True
        )
    ),
):
    """Delete a workflow file from a job script template by id or identifier."""
    logger.debug(f"Deleting workflow file from job script template {id_or_identifier=}")
    async with crud_service.ensure_attribute(
        id_or_identifier,
        owner_email=secure_session.identity_payload.email,
    ) as s:
        job_script_template = await s.get(id_or_identifier)
    workflow_file = await workflow_file_service.get(job_script_template.id, WORKFLOW_FILE_NAME)
    await workflow_file_service.delete(workflow_file)


@router.delete(
    "/upload/garbage-collector",
    status_code=status.HTTP_202_ACCEPTED,
    description="Endpoint to delete all unused files from the job script template file storage",
    tags=["Garbage collector"],
)
async def job_script_template_garbage_collector(
    background_tasks: BackgroundTasks,
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_TEMPLATES_EDIT)),
    bucket=Depends(s3_bucket),
):
    """Delete all unused files from jobbergate templates on the file storage."""
    logger.info("Starting garbage collection from jobbergate file storage")
    background_tasks.add_task(
        garbage_collect,
        secure_session.session,
        bucket,
        [JobScriptTemplateFile, WorkflowFile],
        background_tasks,
    )
    return {"description": "Garbage collection started"}
