#  *******************************************************************************
#  Copyright (c) 2023-2024 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

from __future__ import annotations

import asyncio
import logging
import os.path
from typing import Annotated

import typer
from rich import print
from rich.tree import Tree

from .actions import ActionRef
from .github import GitHubAPI
from .log import setup_logging

app = typer.Typer()


@app.command()
def dependencies(
    workflow: Annotated[str, typer.Argument(help="Workflow to process")],
    resolve_pinned_versions: Annotated[
        bool,
        typer.Option("-r", help="Resolve version."),
    ] = False,
    token: Annotated[
        str | None,
        typer.Option(help="GitHub token to use."),
    ] = None,
    verbose: bool = typer.Option(False, help="Enable verbose output"),
) -> None:
    """
    Print transitive workflow dependencies.
    """
    setup_logging(level=logging.DEBUG if verbose else logging.INFO)

    if os.path.exists(workflow) and workflow.endswith((".yml", ".yaml")):
        workflow = os.path.abspath(workflow)

    print(f"Reading workflow: [bold]{workflow}[/]")
    print()

    action_ref = ActionRef.of_pattern(workflow)
    tree = asyncio.run(_create_tree(action_ref, resolve_pinned_versions, token))
    print(tree)


async def _create_tree(action: ActionRef, resolve_pinned_versions: bool, token: str | None) -> Tree:
    async with GitHubAPI(token) as gh_api:
        return await _fill_tree(gh_api, action, resolve_pinned_versions)


async def _fill_tree(
    gh_api: GitHubAPI,
    action: ActionRef,
    resolve_pinned_versions: bool,
    parent: Tree | None = None,
) -> Tree:
    if resolve_pinned_versions is True and action.can_be_pinned():
        pinned_version = await action.pinned_version(gh_api)
        node = Tree(f"{action!r} # {pinned_version}")
    else:
        node = Tree(f"{action!r}")

    if parent is not None:
        parent.add(node)

    workflow_file = await action.workflow_file(gh_api)
    if workflow_file is not None:
        await asyncio.gather(
            *[
                _fill_tree(gh_api, ActionRef.of_pattern(dep), resolve_pinned_versions, node)
                for dep in sorted(workflow_file.used_actions)
            ]
        )

    return node
