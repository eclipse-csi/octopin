#  *******************************************************************************
#  Copyright (c) 2024 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

import logging

from rich.console import Console
from rich.logging import RichHandler

from . import __appname__

CONSOLE_STDERR = Console(stderr=True)


def setup_logging(terminal_width: int | None = None, level: int = logging.INFO) -> None:
    logger = logging.getLogger(__appname__)
    console = Console(width=terminal_width) if terminal_width else None
    rich_handler = RichHandler(
        show_time=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True,
        show_path=True,
        console=console,
    )
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(rich_handler)

    logger.setLevel(level)
    logger.propagate = False


def print_exception(exc: Exception) -> None:
    import asyncio

    from rich.traceback import Traceback

    rich_tb = Traceback.from_exception(
        type(exc),
        exc,
        exc.__traceback__,
        show_locals=False,
        suppress=[asyncio],
        width=None,
    )

    CONSOLE_STDERR.print(rich_tb)
