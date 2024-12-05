#  *******************************************************************************
#  Copyright (c) 2024 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

import unittest

from parameterized import parameterized

from octopin.actions import ActionRef, ReusableWorkflow


class ReusableWorkflowTestCase(unittest.TestCase):
    @parameterized.expand(  # type: ignore
        [
            "owner/repo/path/to/workflow.yml@v1",
            "owner/repo/path/to/workflow.yml",
            "./path/to/workflow.yaml",
        ]
    )
    def test_create(self, pattern: str) -> None:
        action_ref = ActionRef.of_pattern(pattern)
        self.assertTrue(isinstance(action_ref, ReusableWorkflow))
