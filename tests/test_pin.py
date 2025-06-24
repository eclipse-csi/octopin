#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

import pytest

from octopin.pin import pin_action_on_line_if_needed

_pinned_actions: dict[str, str] = {
    "actions/checkout@v4": "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2"
}


@pytest.mark.parametrize(
    "line, expected",
    [
        # commented out lines should not be pinned
        (
            "#        uses: actions/checkout@v4",
            "#        uses: actions/checkout@v4",
        ),
        # nominal case, w/o leading '-'
        (
            "        uses: actions/checkout@v4",
            "        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2",
        ),
        # nominal case, with leading '-'
        (
            "      - uses: actions/checkout@v4",
            "      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2",
        ),
        # replace existing comment with actual version being pinned
        (
            "      - uses: actions/checkout@v4 # v4",
            "      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2",
        ),
        # ignore action due to comment, does not exist in pinned actions
        (
            "      - uses: mysuperduperorg/mysuperduperaction@v4  # pinning: ignore",
            "      - uses: mysuperduperorg/mysuperduperaction@v4  # pinning: ignore",
        ),
        # ignore action due to comment, exists in pinned actions
        (
            "      - uses: actions/checkout@v4  # pinning: ignore",
            "      - uses: actions/checkout@v4  # pinning: ignore",
        ),
    ],
)
def test_pin_action_on_line_if_needed(line: str, expected: str) -> None:
    assert pin_action_on_line_if_needed(line, _pinned_actions) == expected
