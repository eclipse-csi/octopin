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
import os
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from semver import Version

from .workflow_file import WorkflowFile

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .github import GitHubAPI

_logger = logging.getLogger(__name__)


class ActionRef(ABC):
    @abstractmethod
    def can_be_pinned(self) -> bool:
        pass

    @abstractmethod
    async def pin(self, gh_api: GitHubAPI) -> tuple[str, ActionRef, str]:
        pass

    async def pinned_version(self, gh_api: GitHubAPI) -> str | None:
        return None

    @abstractmethod
    async def workflow_file(self, gh_api: GitHubAPI) -> WorkflowFile | None:
        pass

    @classmethod
    def of_pattern(cls, pattern: str) -> ActionRef:
        return next(c for c in cls.__subclasses__() if c._matches_pattern(pattern))._of(pattern)

    @classmethod
    @abstractmethod
    def _matches_pattern(cls, pattern: str) -> bool:
        pass

    @classmethod
    @abstractmethod
    def _of(cls, pattern: str) -> ActionRef:
        pass


@dataclasses.dataclass(frozen=True)
class ReusableWorkflow(ActionRef):
    file_path: str
    owner: str | None = None
    repo: str | None = None
    ref: str | None = None

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"(([^/]+)/([^@/]+)/)?([^@]+(?:\.yaml|\.yml))(@([^#\s]+))?")

    def can_be_pinned(self) -> bool:
        return self.owner is not None and self.repo is not None and self.ref is not None

    async def pin(self, gh_api: GitHubAPI) -> tuple[str, ActionRef, str]:
        if self.owner is None or self.repo is None or self.ref is None:
            raise RuntimeError(f"cant pin '{self!r}'")

        pinned_reference, comment = await _pin_github_repo(gh_api, self.owner, self.repo, self.ref)
        pinned_action = dataclasses.replace(self, ref=pinned_reference)
        return f"{self!r}", pinned_action, comment

    async def pinned_version(self, gh_api: GitHubAPI) -> str | None:
        if self.owner is None or self.repo is None or self.ref is None:
            raise RuntimeError(f"cant pin '{self!r}'")

        return await _get_pinned_version(gh_api, self.owner, self.repo, self.ref)

    async def workflow_file(self, gh_api: GitHubAPI) -> WorkflowFile | None:
        if self.owner is not None and self.repo is not None:
            version = self.ref
            if version is None:
                version = await gh_api.get_default_branch(self.owner, self.repo)

            status, content = await gh_api.get_content(self.owner, self.repo, version, self.file_path)
            if status == 200:
                return WorkflowFile(content)
            else:
                raise RuntimeError(f"failed to get workflow content for '{self!r}': {content}")
        else:
            with open(self.file_path) as file:
                return WorkflowFile(file.read())

    @classmethod
    def _matches_pattern(cls, pattern: str) -> bool:
        return cls._PATTERN.match(pattern) is not None

    @classmethod
    def _of(cls, action_ref: str) -> ReusableWorkflow:
        if os.path.exists(action_ref):
            return cls(action_ref)

        match = cls._PATTERN.match(action_ref)
        if match is not None:
            owner = match.group(2)
            repo = match.group(3)
            path = match.group(4)
            reference = match.group(6)
            return cls(path, owner, repo, reference)
        else:
            raise ValueError(f"no match for {cls}: '{action_ref}'")

    def __repr__(self) -> str:
        if self.owner is not None and self.repo is not None:
            result = self.owner + "/" + self.repo + "/" + self.file_path
            if self.ref is not None:
                result += "@" + self.ref
            return result
        else:
            return self.file_path


@dataclasses.dataclass(frozen=True)
class GHAction(ActionRef):
    owner: str
    repo: str
    ref: str | None = None
    path: str | None = None

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"([^\\.][^/]+)/([^@/]+)(/([^@]+))?(@([^#\s]+))?")

    def can_be_pinned(self) -> bool:
        return True

    async def pin(self, gh_api: GitHubAPI) -> tuple[str, ActionRef, str]:
        if self.owner is None or self.repo is None or self.ref is None:
            raise RuntimeError(f"cant pin '{self!r}'")

        pinned_reference, comment = await _pin_github_repo(gh_api, self.owner, self.repo, self.ref)
        pinned_action = dataclasses.replace(self, ref=pinned_reference)
        return f"{self!r}", pinned_action, comment

    async def pinned_version(self, gh_api: GitHubAPI) -> str | None:
        if self.owner is None or self.repo is None or self.ref is None:
            raise RuntimeError(f"cant pin '{self!r}'")

        return await _get_pinned_version(gh_api, self.owner, self.repo, self.ref)

    async def workflow_file(self, gh_api: GitHubAPI) -> WorkflowFile | None:
        version = self.ref
        if version is None:
            version = await gh_api.get_default_branch(self.owner, self.repo)

        def get_action_entry(extension: str) -> str:
            if self.path is None:
                return f"action.{extension}"
            else:
                return self.path + f"/action.{extension}"

        for ext in ["yml", "yaml"]:
            content_path = get_action_entry(ext)

            status, content = await gh_api.get_content(self.owner, self.repo, version, content_path)
            if status == 200:
                return WorkflowFile(content)
            elif status == 404:
                continue
            else:
                raise RuntimeError(f"received status '{status}' while retrieving action '{self!r}'")

        raise RuntimeError(f"failed to retrieve action '{self!r}'")

    @classmethod
    def _matches_pattern(cls, pattern: str) -> bool:
        return cls._PATTERN.match(pattern) is not None

    @classmethod
    def _of(cls, action_ref: str) -> GHAction:
        match = cls._PATTERN.match(action_ref)
        if match is not None:
            owner = match.group(1)
            repo = match.group(2)
            path = match.group(4)
            reference = match.group(6)
            return cls(owner, repo, reference, path)
        else:
            raise ValueError(f"no match for {cls}: '{action_ref}'")

    def __repr__(self) -> str:
        result = self.owner + "/" + self.repo
        if self.path is not None:
            result += "/" + self.path
        if self.ref is not None:
            result += "@" + self.ref
        return result


@dataclasses.dataclass
class LocalGHAction(ActionRef):
    path: str

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"(\./[^@]+)")

    def can_be_pinned(self) -> bool:
        return False

    async def pin(self, gh_api: GitHubAPI) -> tuple[str, ActionRef, str]:
        raise RuntimeError(f"cant pin {self!r}")

    async def workflow_file(self, gh_api: GitHubAPI) -> WorkflowFile | None:
        if os.path.exists(self.path):
            for ext in ["yml", "yaml"]:
                content_path = os.path.join(self.path, f"action.{ext}")

                if os.path.exists(content_path):
                    with open(content_path) as file:
                        return WorkflowFile(file.read())

            return None
        else:
            return None

    @classmethod
    def _matches_pattern(cls, pattern: str) -> bool:
        return cls._PATTERN.match(pattern) is not None

    @classmethod
    def _of(cls, action_ref: str) -> LocalGHAction:
        match = cls._PATTERN.match(action_ref)
        if match is not None:
            path = match.group(1)
            return cls(path)
        else:
            raise ValueError(f"no match for {cls}: '{action_ref}'")

    def __repr__(self) -> str:
        return self.path


@dataclasses.dataclass
class DockerAction(ActionRef):
    image: str
    host: str | None = None
    tag: str | None = None

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"docker://((.+)/)?([^:/]+)(:([^#\s]+))?")

    def can_be_pinned(self) -> bool:
        # can't pin docker actions atm.
        return False

    async def pin(self, gh_api: GitHubAPI) -> tuple[str, ActionRef, str]:
        raise RuntimeError(f"cant pin {self!r}")

    async def workflow_file(self, gh_api: GitHubAPI) -> WorkflowFile | None:
        return None

    @classmethod
    def _matches_pattern(cls, pattern: str) -> bool:
        return cls._PATTERN.match(pattern) is not None

    @classmethod
    def _of(cls, action_ref: str) -> DockerAction:
        match = cls._PATTERN.match(action_ref)
        if match is not None:
            host = match.group(2)
            image = match.group(3)
            tag = match.group(5)
            return cls(image, host, tag)
        else:
            raise ValueError(f"no match for {cls}: '{action_ref}'")

    def __repr__(self) -> str:
        result = "docker://"
        if self.host is not None:
            result += self.host + "/"
        result += self.image
        if self.tag is not None:
            result += ":" + self.tag
        return result


async def _get_pinned_version(gh_api: GitHubAPI, owner: str, repo: str, reference: str) -> str | None:
    tags_of_repo = await gh_api.get_tags(owner, repo)
    branches_of_repo = await gh_api.get_branches(owner, repo)

    refs_by_commit: dict[str, Any] = {}

    def semver_from_ref_name(ref_name: str) -> Version | None:
        match = re.match(r"v(\d+)(\.(\d+)\.(\d+))?", ref_name)
        if match is not None:
            major = int(match.group(1))
            minor = int(match.group(3)) if match.group(3) is not None else 0
            patch = int(match.group(4)) if match.group(4) is not None else 0

            return Version(major, minor, patch)
        else:
            return None

    def update_latest(ref: Mapping[str, Any]) -> None:
        ref_name = ref["name"]
        sha = ref["commit"]["sha"]
        current = refs_by_commit.get(sha)
        if current is not None:
            ref_version = semver_from_ref_name(ref_name)
            curr_version = semver_from_ref_name(current["name"])

            if ref_version is not None and curr_version is not None:
                if ref_version.compare(curr_version) <= 0:
                    return

        refs_by_commit[sha] = ref

    for b in branches_of_repo:
        update_latest(b)
    for t in tags_of_repo:
        update_latest(t)

    if reference in refs_by_commit:
        return str(refs_by_commit[reference]["name"])
    else:
        return None


async def _pin_github_repo(gh_api: GitHubAPI, owner: str, repo: str, reference: str) -> tuple[str, str]:
    tags_of_repo = await gh_api.get_tags(owner, repo)
    branches_of_repo = await gh_api.get_branches(owner, repo)

    refs_by_name: dict[str, Any] = {b["name"]: b for b in branches_of_repo}
    for t in tags_of_repo:
        refs_by_name[t["name"]] = t

    def semver_from_ref_name(ref_name: str) -> Version | None:
        match = re.match(r"v(\d+)(\.(\d+)\.(\d+))?", ref_name)
        if match is not None:
            major = int(match.group(1))
            minor = int(match.group(3)) if match.group(3) is not None else 0
            patch = int(match.group(4)) if match.group(4) is not None else 0

            return Version(major, minor, patch)
        else:
            return None

    refs_by_commit: dict[str, Any] = {}

    def update_latest(ref: Mapping[str, Any]) -> None:
        ref_name = ref["name"]
        sha = ref["commit"]["sha"]
        current = refs_by_commit.get(sha)
        if current is not None:
            ref_version = semver_from_ref_name(ref_name)
            curr_version = semver_from_ref_name(current["name"])

            if ref_version is not None and curr_version is not None:
                if ref_version.compare(curr_version) <= 0:
                    return

        refs_by_commit[sha] = ref

    for b in branches_of_repo:
        update_latest(b)
    for t in tags_of_repo:
        update_latest(t)

    tags_by_major: dict[str, Any] = {}

    for name, tag in refs_by_name.items():
        semver = semver_from_ref_name(name)
        if semver is not None:
            tag["semver"] = semver
            refname_major = f"v{semver.major}"
            latest_version_grouped_by_major = tags_by_major.get(refname_major, Version(0))
            if semver.compare(latest_version_grouped_by_major) > 0:
                tags_by_major[refname_major] = semver
        else:
            tag["semver"] = Version(0)

    version = "v" + str(tags_by_major[reference]) if reference in tags_by_major else reference

    if version in refs_by_name:
        tag = refs_by_name[version]
    elif version in refs_by_commit:
        tag = refs_by_commit[version]
    else:
        tag = None

    if tag is not None:
        return tag["commit"]["sha"], tag["name"]
    else:
        return reference, ""
