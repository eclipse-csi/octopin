#  *******************************************************************************
#  Copyright (c) 2023-2024 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

from __future__ import annotations

import dataclasses
import logging
from functools import cached_property
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator

_logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class WorkflowFile:
    raw_content: str
    content: dict[str, Any] = dataclasses.field(init=False)
    lines: list[str] = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "content", yaml.safe_load(self.raw_content))
        object.__setattr__(self, "lines", self.raw_content.splitlines(keepends=True))

    @cached_property
    def used_actions(self) -> Iterator[str]:
        # regular workflows
        for job_id, v in self.content.get("jobs", {}).items():
            # jobs.<job_id>.steps[*].uses
            for step_index, step in enumerate(v.get("steps", [])):
                if "uses" in step:
                    action = step["uses"]
                    _logger.debug("found action in jobs.%s.steps[%d].uses = '%s'", job_id, step_index, action)
                    yield action

            # jobs.<job_id>.uses
            if "uses" in v:
                action = v["uses"]
                _logger.debug("found action in jobs.%s.uses = '%s'", job_id, action)
                yield action

        # composite actions
        if "runs" in self.content:
            # runs.steps[*].uses
            for step_index, step in enumerate(self.content["runs"].get("steps", [])):
                if "uses" in step:
                    action = step["uses"]
                    _logger.debug("found action in runs.steps[%d].uses = '%s'", step_index, action)
                    yield action
