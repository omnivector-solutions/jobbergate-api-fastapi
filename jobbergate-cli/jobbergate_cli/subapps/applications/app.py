"""
Provide a ``typer`` app that can interact with Application data in a cruddy manner.
"""

import pathlib
from textwrap import dedent
from typing import Any, Dict, Optional, cast

import typer

from jobbergate_cli.constants import SortOrder
from jobbergate_cli.exceptions import Abort, handle_abort, handle_authentication_error
from jobbergate_cli.render import StyleMapper, render_single_result, terminal_message
from jobbergate_cli.requests import make_request
from jobbergate_cli.schemas import ApplicationResponse, JobbergateContext
from jobbergate_cli.subapps.applications.tools import fetch_application_data, save_application_files, upload_application
from jobbergate_cli.subapps.pagination import handle_pagination


# TODO: move hidden field logic to the API
HIDDEN_FIELDS = [
    "cloned_from_id",
    "created_at",
    "is_archived",
    "template_files",
    "template_vars",
    "updated_at",
    "workflow_files",
]

ID_NOTE = """

    This id represents the primary key of the application in the database. It
    will always be a unique integer and is automatically generated by the server
    when an Application is created. All applications receive an id, so it may
    be used to target a specific instance of an application whether or not it
    is provided with a human-friendly "identifier".
"""


IDENTIFIER_NOTE = """

    The identifier allows the user to access commonly used applications with a
    friendly name that is easy to remember. Identifiers should only be used
    for applications that are frequently used or should be easy to find in the list.
    An identifier may be added, removed, or changed on an existing application.
"""


style_mapper = StyleMapper(
    application_id="green",
    name="cyan",
    identifier="magenta",
)


app = typer.Typer(help="Commands to interact with applications")


@app.command("list")
@handle_abort
@handle_authentication_error
def list_all(
    ctx: typer.Context,
    show_all: bool = typer.Option(False, "--all", help="Show all applications, even the ones without identifier"),
    user_only: bool = typer.Option(False, "--user", help="Show only applications owned by the current user"),
    search: Optional[str] = typer.Option(None, help="Apply a search term to results"),
    sort_order: SortOrder = typer.Option(SortOrder.DESCENDING, help="Specify sort order"),
    sort_field: Optional[str] = typer.Option("id", help="The field by which results should be sorted"),
):
    """
    Show available applications
    """
    jg_ctx: JobbergateContext = ctx.obj

    # Make static type checkers happy
    assert jg_ctx is not None
    assert jg_ctx.client is not None

    params: Dict[str, Any] = dict(
        include_null_identifier=show_all,
        user_only=user_only,
    )
    if search is not None:
        params["search"] = search
    if sort_order is not SortOrder.UNSORTED:
        params["sort_ascending"] = sort_order is SortOrder.ASCENDING
    if sort_field is not None:
        params["sort_field"] = sort_field

    handle_pagination(
        jg_ctx=jg_ctx,
        url_path="/jobbergate/job-script-templates",
        abort_message="Couldn't retrieve applications list from API",
        params=params,
        title="Applications List",
        style_mapper=style_mapper,
        hidden_fields=HIDDEN_FIELDS,
        nested_response_model_cls=ApplicationResponse,
    )


@app.command()
@handle_abort
@handle_authentication_error
def get_one(
    ctx: typer.Context,
    id: Optional[int] = typer.Option(
        None,
        "--id",
        "-i",
        help=f"The specific id of the application. {ID_NOTE}",
    ),
    identifier: Optional[str] = typer.Option(
        None,
        help=f"The human-friendly identifier of the application. {IDENTIFIER_NOTE}",
    ),
):
    """
    Get a single application by id or identifier
    """
    jg_ctx: JobbergateContext = ctx.obj
    result = fetch_application_data(jg_ctx, id=id, identifier=identifier)
    render_single_result(
        jg_ctx,
        result,
        hidden_fields=HIDDEN_FIELDS,
        title="Application",
    )


@app.command()
@handle_abort
@handle_authentication_error
def create(
    ctx: typer.Context,
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="The name of the application to create",
    ),
    identifier: Optional[str] = typer.Option(
        None,
        help=f"The human-friendly identifier of the application. {IDENTIFIER_NOTE}",
    ),
    application_path: pathlib.Path = typer.Option(
        ...,
        "--application-path",
        "-a",
        help="The path to the directory where the application files are located",
    ),
    application_desc: Optional[str] = typer.Option(
        None,
        help="A helpful description of the application",
    ),
):
    """
    Create a new application.
    """
    req_data = dict()
    req_data["name"] = name
    if identifier:
        req_data["identifier"] = identifier

    if application_desc:
        req_data["description"] = application_desc

    jg_ctx: JobbergateContext = ctx.obj

    # Make static type checkers happy
    assert jg_ctx.client is not None

    result = cast(
        Dict[str, Any],
        make_request(
            jg_ctx.client,
            "/jobbergate/job-script-templates",
            "POST",
            expected_status=201,
            abort_message="Request to create application was not accepted by the API",
            support=True,
            json=req_data,
        ),
    )
    application_id = result["id"]
    result["application_uploaded"] = False

    try:
        if application_path is not None:
            upload_application(jg_ctx, application_path, application_id=application_id, application_identifier=None)
            result["application_uploaded"] = True
    except Abort as e:
        raise e
    finally:
        if not result["application_uploaded"]:
            terminal_message(
                """
                The application files could not be uploaded.

                Try running the `update` command including the application path to re-upload.
                """,
                subject="File upload failed",
                color="yellow",
            )
        render_single_result(
            jg_ctx,
            result,
            hidden_fields=HIDDEN_FIELDS,
            title="Created Application",
        )


@app.command()
@handle_abort
@handle_authentication_error
def update(
    ctx: typer.Context,
    id: Optional[int] = typer.Option(
        None,
        "--id",
        "-i",
        help=f"The specific id of the application to update. {ID_NOTE}",
    ),
    identifier: Optional[str] = typer.Option(
        None,
        help=f"The human-friendly identifier of the application to update. {IDENTIFIER_NOTE}",
    ),
    application_path: Optional[pathlib.Path] = typer.Option(
        None,
        "--application-path",
        "-a",
        help="The path to the directory where the application files are located",
    ),
    update_identifier: Optional[str] = typer.Option(
        None,
        help="Optional new application identifier to be set",
    ),
    application_desc: Optional[str] = typer.Option(
        None,
        help="Optional new application description to be set",
    ),
    application_name: Optional[str] = typer.Option(
        None,
        help="Optional new application name to be set",
    ),
):
    """
    Update an existing application.
    """
    identification: Any = id
    if id is None and identifier is None:
        terminal_message(
            """
            You must supply either [yellow]id[/yellow] or [yellow]identifier[/yellow].
            """,
            subject="Invalid params",
        )
        raise typer.Exit()
    elif id is not None and identifier is not None:
        terminal_message(
            """
            You may not supply both [yellow]id[/yellow] and [yellow]identifier[/yellow].
            """,
            subject="Invalid params",
        )
        raise typer.Exit()
    elif identifier is not None:
        identification = identifier

    req_data = dict()

    if update_identifier:
        req_data["identifier"] = update_identifier

    if application_desc:
        req_data["description"] = application_desc

    if application_name:
        req_data["name"] = application_name

    jg_ctx: JobbergateContext = ctx.obj

    # Make static type checkers happy
    assert jg_ctx.client is not None

    if req_data:
        make_request(
            jg_ctx.client,
            f"/jobbergate/job-script-templates/{identification}",
            "PUT",
            expect_response=False,
            abort_message="Request to update application was not accepted by the API",
            support=True,
            json=req_data,
            expected_status=200,
        )

    try:
        if application_path is not None:
            upload_application(jg_ctx, application_path, application_id=id, application_identifier=identifier)
    except Abort as e:
        terminal_message(
            "The application files could not be uploaded.",
            subject="File upload failed",
            color="yellow",
        )
        raise e
    finally:
        if not id and update_identifier:
            # We need to fetch from new identifier if it was updated
            identifier = update_identifier
        result = fetch_application_data(jg_ctx, id=id, identifier=identifier)

        render_single_result(
            jg_ctx,
            result,
            hidden_fields=HIDDEN_FIELDS,
            title="Updated Application",
        )


@app.command()
@handle_abort
@handle_authentication_error
def delete(
    ctx: typer.Context,
    id: Optional[int] = typer.Option(
        None,
        "--id",
        "-i",
        help=f"The specific id of the application to delete. {ID_NOTE}",
    ),
    identifier: Optional[str] = typer.Option(
        None,
        help=f"The human-friendly identifier of the application to update. {IDENTIFIER_NOTE}",
    ),
):
    """
    Delete an existing application.
    """
    jg_ctx: JobbergateContext = ctx.obj

    # Make static type checkers happy
    assert jg_ctx.client is not None

    identification: Any = id
    if id is None and identifier is None:
        terminal_message(
            """
            You must supply either [yellow]id[/yellow] or [yellow]identifier[/yellow].
            """,
            subject="Invalid params",
        )
        raise typer.Exit()
    elif id is not None and identifier is not None:
        terminal_message(
            """
            You may not supply both [yellow]id[/yellow] and [yellow]identifier[/yellow].
            """,
            subject="Invalid params",
        )
        raise typer.Exit()
    elif identifier is not None:
        identification = identifier

    # Delete the upload. The API will also remove the application data files
    make_request(
        jg_ctx.client,
        f"/jobbergate/job-script-templates/{identification}",
        "DELETE",
        expected_status=204,
        expect_response=False,
        abort_message="Request to delete application was not accepted by the API",
        support=True,
    )
    terminal_message(
        """
        The application was successfully deleted.
        """,
        subject="Application delete succeeded",
    )


@app.command()
@handle_abort
@handle_authentication_error
def download_files(
    ctx: typer.Context,
    id: Optional[int] = typer.Option(
        None,
        help=f"The specific id of the application. {ID_NOTE}",
    ),
    identifier: Optional[str] = typer.Option(
        None,
        help=f"The human-friendly identifier of the application. {IDENTIFIER_NOTE}",
    ),
):
    """
    Download the files from an application to the current working directory.
    """
    jg_ctx: JobbergateContext = ctx.obj

    result = fetch_application_data(jg_ctx, id=id, identifier=identifier)
    saved_files = save_application_files(
        jg_ctx,
        application_data=result,
        destination_path=pathlib.Path.cwd(),
    )
    terminal_message(
        dedent(
            """
            A total of {} application files were successfully downloaded.
            """.format(len(saved_files))
        ).strip(),
        subject="Application download succeeded",
    )


@app.command()
@handle_abort
@handle_authentication_error
def clone(
    ctx: typer.Context,
    id: Optional[int] = typer.Option(
        None,
        help=f"The specific id of the application. {ID_NOTE}",
    ),
    identifier: Optional[str] = typer.Option(
        None,
        help=f"The human-friendly identifier of the application. {IDENTIFIER_NOTE}",
    ),
    application_identifier: Optional[str] = typer.Option(
        None,
        help="""
        Optional new application identifier to override the original.

        Notice this can not match an existing identifier, including the one this entry is going to be cloned from.
        """,
    ),
    application_desc: Optional[str] = typer.Option(
        None,
        help="Optional new application description to override the original",
    ),
    application_name: Optional[str] = typer.Option(
        None,
        help="Optional new application name to override the original",
    ),
):
    """
    Clone an application, so the user can own and modify a copy of it.
    """
    identification: Any = id
    if id is None and identifier is None:
        terminal_message(
            """
            You must supply either [yellow]id[/yellow] or [yellow]identifier[/yellow].
            """,
            subject="Invalid params",
        )
        raise typer.Exit()
    elif id is not None and identifier is not None:
        terminal_message(
            """
            You may not supply both [yellow]id[/yellow] and [yellow]identifier[/yellow].
            """,
            subject="Invalid params",
        )
        raise typer.Exit()
    elif identifier is not None:
        identification = identifier

    req_data = dict()

    if application_identifier:
        req_data["identifier"] = application_identifier

    if application_desc:
        req_data["description"] = application_desc

    if application_name:
        req_data["name"] = application_name

    jg_ctx: JobbergateContext = ctx.obj

    # Make static type checkers happy
    assert jg_ctx.client is not None

    result = cast(
        ApplicationResponse,
        make_request(
            jg_ctx.client,
            f"/jobbergate/job-script-templates/clone/{identification}",
            "POST",
            json=req_data,
            expected_status=201,
            abort_message=f"Couldn't clone application {identification} from API",
            response_model_cls=ApplicationResponse,
            support=True,
        ),
    )

    render_single_result(
        jg_ctx,
        result,
        hidden_fields=HIDDEN_FIELDS,
        title="Cloned Application",
    )
