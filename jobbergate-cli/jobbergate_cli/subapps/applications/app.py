"""
Provide a ``typer`` app that can interact with Application data in a cruddy manner.
"""

import pathlib
from textwrap import dedent
from typing import Any, Dict, Optional, cast

import typer

from jobbergate_cli.constants import OV_CONTACT, SortOrder
from jobbergate_cli.exceptions import handle_abort
from jobbergate_cli.render import (
    StyleMapper,
    render_list_results,
    render_single_result,
    terminal_confirm,
    terminal_message,
)
from jobbergate_cli.requests import make_request
from jobbergate_cli.schemas import JobbergateContext, ListResponseEnvelope
from jobbergate_cli.subapps.applications.tools import (
    fetch_application_data,
    load_default_config,
    save_application_files,
    upload_application,
)


# TODO: move hidden field logic to the API
HIDDEN_FIELDS = [
    "application_config",
    "application_source_file",
    "application_templates",
    "created_at",
    "updated_at",
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
    id="green",
    application_name="cyan",
    application_identifier="magenta",
)


app = typer.Typer(help="Commands to interact with applications")


@app.command("list")
@handle_abort
def list_all(
    ctx: typer.Context,
    show_all: bool = typer.Option(False, "--all", help="Show all applications, even the ones without identifier"),
    user_only: bool = typer.Option(False, "--user", help="Show only applications owned by the current user"),
    search: Optional[str] = typer.Option(None, help="Apply a search term to results"),
    sort_order: SortOrder = typer.Option(SortOrder.UNSORTED, help="Specify sort order"),
    sort_field: Optional[str] = typer.Option(None, help="The field by which results should be sorted"),
):
    """
    Show available applications
    """
    jg_ctx: JobbergateContext = ctx.obj

    # Make static type checkers happy
    assert jg_ctx is not None
    assert jg_ctx.client is not None

    params: Dict[str, Any] = dict(
        all=show_all,
        user=user_only,
    )
    if search is not None:
        params["search"] = search
    if sort_order is not SortOrder.UNSORTED:
        params["sort_ascending"] = SortOrder is SortOrder.ASCENDING
    if sort_field is not None:
        params["sort_field"] = sort_field

    envelope = cast(
        ListResponseEnvelope,
        make_request(
            jg_ctx.client,
            "/jobbergate/applications",
            "GET",
            expected_status=200,
            abort_message="Couldn't retrieve applications list from API",
            support=True,
            response_model_cls=ListResponseEnvelope,
            params=params,
        ),
    )
    render_list_results(
        jg_ctx,
        envelope,
        title="Applications List",
        style_mapper=style_mapper,
        hidden_fields=HIDDEN_FIELDS,
    )


@app.command()
@handle_abort
def get_one(
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
def create(
    ctx: typer.Context,
    name: str = typer.Option(
        ...,
        help="The name of the application to create",
    ),
    identifier: Optional[str] = typer.Option(
        None,
        help=f"The human-friendly identifier of the application. {IDENTIFIER_NOTE}",
    ),
    application_path: pathlib.Path = typer.Option(
        ...,
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
    req_data = load_default_config()
    req_data["application_name"] = name
    if identifier:
        req_data["application_identifier"] = identifier

    if application_desc:
        req_data["application_description"] = application_desc

    jg_ctx: JobbergateContext = ctx.obj

    # Make static type checkers happy
    assert jg_ctx.client is not None

    result = cast(
        Dict[str, Any],
        make_request(
            jg_ctx.client,
            "/jobbergate/applications",
            "POST",
            expected_status=201,
            abort_message="Request to create application was not accepted by the API",
            support=True,
            json=req_data,
        ),
    )
    application_id = result["id"]

    successful_upload = upload_application(jg_ctx, application_path, application_id)
    if not successful_upload:
        terminal_message(
            f"""
            The application files could not be uploaded.

            Try running the `update` command including the application path to re-upload.

            [yellow]If the problem persists, please contact [bold]{OV_CONTACT}[/bold]
            for support and trouble-shooting[/yellow]
            """,
            subject="File upload failed",
            color="yellow",
        )
    else:
        result["application_uploaded"] = True

    render_single_result(
        jg_ctx,
        result,
        hidden_fields=HIDDEN_FIELDS,
        title="Created Application",
    )


@app.command()
@handle_abort
def update(
    ctx: typer.Context,
    id: int = typer.Option(
        ...,
        help=f"The specific id of the application to update. {ID_NOTE}",
    ),
    application_path: Optional[pathlib.Path] = typer.Option(
        None,
        help="The path to the directory where the application files are located",
    ),
    identifier: Optional[str] = typer.Option(
        None,
        help="Optional new application identifier to be set",
    ),
    application_desc: Optional[str] = typer.Option(
        None,
        help="Optional new application description to be set",
    ),
):
    """
    Update an existing application.
    """
    req_data = dict()

    if identifier:
        req_data["application_identifier"] = identifier

    if application_desc:
        req_data["application_description"] = application_desc

    jg_ctx: JobbergateContext = ctx.obj

    # Make static type checkers happy
    assert jg_ctx.client is not None

    result = cast(
        Dict[str, Any],
        make_request(
            jg_ctx.client,
            f"/jobbergate/applications/{id}",
            "PUT",
            expected_status=200,
            abort_message="Request to update application was not accepted by the API",
            support=True,
            json=req_data,
        ),
    )

    if application_path is not None:
        successful_upload = upload_application(jg_ctx, application_path, id)
        if not successful_upload:
            terminal_message(
                f"""
                The application files could not be uploaded.

                [yellow]If the problem persists, please contact [bold]{OV_CONTACT}[/bold]
                for support and trouble-shooting[/yellow]
                """,
                subject="File upload failed",
                color="yellow",
            )
        else:
            result["application_uploaded"] = True

    render_single_result(
        jg_ctx,
        result,
        hidden_fields=HIDDEN_FIELDS,
        title="Updated Application",
    )


@app.command()
@handle_abort
def delete(
    ctx: typer.Context,
    id: int = typer.Option(
        ...,
        help=f"the specific id of the application to delete. {ID_NOTE}",
    ),
    confirm: bool = typer.Option(
        None,
        "--confirm",
        "-y",
        help="If supplied, do not ask for confirmation; just delete.",
    ),
):
    """
    Delete an existing application.
    """
    if not confirm and not terminal_confirm(
        """
        [yellow]Any files uploaded for this Application will be completely removed.
        Any references to it in other items will also be removed.
        """,
        subject="Deleting is permanent!",
        color="red",
    ):
        terminal_message(
            """
            No application was deleted.
            """,
            subject="Aborted",
            color="yellow",
        )
        return

    jg_ctx: JobbergateContext = ctx.obj

    # Make static type checkers happy
    assert jg_ctx.client is not None

    # Delete the upload. The API will also remove the application data files
    make_request(
        jg_ctx.client,
        f"/jobbergate/applications/{id}",
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
        application_data=result,
        destination_path=pathlib.Path.cwd(),
    )
    terminal_message(
        dedent(
            """
            A total of {} application files were successfully downloaded.
            """.format(
                len(saved_files)
            )
        ).strip(),
        subject="Application download succeeded",
    )
