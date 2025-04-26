#  *******************************************************************************
#  Copyright (c) 2023-2024 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

from __future__ import annotations

import asyncio
import difflib
import logging
import os.path
import re
from typing import TYPE_CHECKING, Annotated

import typer
from rich import print

from .actions import ActionRef
from .github import GitHubAPI

if TYPE_CHECKING:
    from .workflow_file import WorkflowFile

app = typer.Typer()

_logger = logging.getLogger(__name__)


def _pin(
    workflow: Annotated[str, typer.Argument(help="Workflow to process")],
    diff_mode: Annotated[
        bool,
        typer.Option("--diff", "-d", help="Show diffs."),
    ] = False,
    inplace_mode: Annotated[
        bool,
        typer.Option(
            "--inplace", "-i", help="Modify input workflow inplace, not taken into account when `--diff` is enabled."
        ),
    ] = False,
    token: Annotated[
        str | None,
        typer.Option(help="GitHub token to use."),
    ] = None,
    verbose: bool = typer.Option(False, help="Enable verbose output"),
) -> int:
    """
    Pin actions used in workflows.
    """
    workflow_ref = ActionRef.of_pattern(workflow)
    workflow_file, pinned_lines = asyncio.run(_handle_async(workflow_ref, token))

    if workflow_file is None:
        return 1

    if diff_mode is True:
        for line in difflib.unified_diff(
            workflow_file.lines, pinned_lines, fromfile="original", tofile="pinned", n=3, lineterm="\n"
        ):
            line = line.rstrip("\n")
            if line.startswith("-"):
                print(f"[ref]{line}[/]")
            elif line.startswith("+"):
                print(f"[green]{line}[/]")
            else:
                print(line)
    else:
        if inplace_mode is True and os.path.exists(workflow):
            with open(workflow, "w") as out:
                for line in pinned_lines:
                    out.write(line)
        else:
            for line in pinned_lines:
                print(line.rstrip("\n"))

    return 0


@app.command()
def pin(
    workflows: Annotated[list[str], typer.Argument(help="Workflow files to process", min=1)],
    diff_mode: Annotated[
        bool,
        typer.Option("--diff", "-d", help="Show diffs."),
    ] = False,
    inplace_mode: Annotated[
        bool,
        typer.Option(
            "--inplace", "-i", help="Modify input workflow inplace, not taken into account when `--diff` is enabled."
        ),
    ] = False,
    token: Annotated[
        str | None,
        typer.Option(
            help="GitHub token to use. Reads GITHUB_TOKEN from the environment if not provided.",
            envvar=["GITHUB_TOKEN", "GH_TOKEN"],
        ),
    ] = None,
    verbose: bool = typer.Option(False, help="Enable verbose output"),
) -> int:
    """
    Pin actions used in multiple workflows by calling `pin` for each workflow.
    """
    if not token:
        print("[yellow]Warn: GitHub token not provided. Proceeding unauthenticated.")

    return_code = 0

    for workflow in workflows:
        print(f"\n[bold]Processing workflow: {workflow}[/]")
        result = _pin(workflow, diff_mode, inplace_mode, token, verbose)
        if result != 0:
            print(f"[red]Failed to process {workflow}[/]")
            return_code = 1  # Mark failure but continue processing

    return return_code


async def _handle_async(workflow_ref: ActionRef, token: str | None) -> tuple[WorkflowFile | None, list[str]]:
    async with GitHubAPI(token) as gh_api:
        workflow_file = await workflow_ref.workflow_file(gh_api)
        if workflow_file is None:
            _logger.error("could not retrieve workflow file")
            return None, []

        actions = set(workflow_file.used_actions)
        pinned_actions = {}

        tasks = []
        for action in actions:
            a = ActionRef.of_pattern(action)
            if a.can_be_pinned():
                tasks.append(a.pin(gh_api))
            else:
                pinned_actions[action] = action

        r = await asyncio.gather(*tasks)

        for orig_action, pinned_action, pinned_comment in r:
            if pinned_comment:
                pinned_actions[orig_action] = f"{pinned_action!r} # {pinned_comment}"
            else:
                pinned_actions[orig_action] = f"{pinned_action!r}"

        def pin(m: re.Match[str]) -> str:
            return str(m.group(2) + pinned_actions[m.group(3)])

        pinned_lines = []
        for line in workflow_file.lines:
            pinned_lines.append(re.sub(r"^[^#\n]*((uses:\s+)([^\s#]+)((\s+#)([^\n]+))?)(?=\n?)", pin, line))

        return workflow_file, pinned_lines


if __name__ == "__main__":
    app()
