#  *******************************************************************************
#  Copyright (c) 2024 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

from typing import Annotated

import typer
from rich import print

from . import __appname__, __version__
from .dependencies import app as dependencies_app
from .log import print_exception
from .pin import app as pin_app

app = typer.Typer(rich_markup_mode="rich")


def version_callback(value: bool) -> None:
    if value:
        print(f"{__appname__} version: [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def callback(
    version: Annotated[
        bool | None,
        typer.Option("--version", help="Show the version and exit.", callback=version_callback),
    ] = None,
) -> None:
    """
    OctoPIN - Tool to pin used actions and analyse transitive dependencies of GitHub workflows / actions.

    Read more in the docs: [link=https://octopin.readthedocs.org/]https://octopin.readthedocs.org/[/link].
    """


app.add_typer(dependencies_app)
app.add_typer(pin_app)


def main() -> None:
    from typer.main import get_command

    try:
        result = get_command(app)()
        print(result)
    except Exception as exc:
        print_exception(exc)
