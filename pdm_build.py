#  *******************************************************************************
#  Copyright (c) 2024 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

from pdm.backend._vendor.packaging.version import Version
from pdm.backend.hooks.version import SCMVersion


def format_version(version: SCMVersion) -> str:
    if str(version.version) == "0.0":
        version = version._replace(version=Version("0.1.0"))
    if version.distance is None:
        return str(version.version)
    else:
        return f"{version.version}.dev{version.distance}"
