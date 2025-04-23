#  *******************************************************************************
#  Copyright (c) 2024 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

import json
import logging
import os
from collections.abc import Mapping
from logging import Logger
from typing import Any, Self

from aiohttp_client_cache.backends.sqlite import SQLiteBackend
from aiohttp_client_cache.session import CachedSession
from platformdirs import user_cache_dir

from . import __appname__


def _get_github_token_from_env() -> str | None:
    return os.getenv("GITHUB_TOKEN")


class GitHubAPI:
    _GH_API_VERSION = "2022-11-28"
    _GH_API_URL_ROOT = "https://api.github.com"

    _GH_HEADERS: Mapping[str, str] = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": _GH_API_VERSION,
    }

    def __init__(self, token: str | None) -> None:
        self._logger = logging.getLogger(__name__)

        cache_dir = user_cache_dir(__appname__)
        cache_file = os.path.join(cache_dir, "http-cache")

        if token is None:
            token = _get_github_token_from_env()

        self._token = token
        self._session = CachedSession(cache=SQLiteBackend(cache_name=cache_file, use_temp=False))

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exception_type, exception_value, exception_traceback) -> None:  # type: ignore
        await self._session.close()

    @property
    def logger(self) -> Logger:
        return self._logger

    def _build_api_url(self, path: str) -> str:
        if not path.startswith("/"):
            raise ValueError(f"path needs to start with a slash: '{path}'")

        return f"{self._GH_API_URL_ROOT}{path}"

    def _add_authorization_header(self, headers: Mapping[str, str]) -> dict[str, str]:
        if self._token is None:
            return dict(headers)
        else:
            new_headers = dict(headers)
            new_headers.update({"Authorization": f"Bearer {self._token}"})
            return new_headers

    async def get_default_branch(self, owner: str, repo: str) -> str:
        self._logger.debug("retrieving default branch for repo '%s/%s'", owner, repo)
        result = await self._request_json("GET", f"/repos/{owner}/{repo}")
        return str(result["default_branch"])

    async def get_tags(self, owner: str, repo: str) -> list[dict[str, Any]]:
        self._logger.debug("retrieving tags for repo '%s/%s'", owner, repo)
        return await self._request_paged_json("GET", f"/repos/{owner}/{repo}/tags")

    async def get_branches(self, owner: str, repo: str) -> list[dict[str, Any]]:
        self._logger.debug("retrieving branches for repo '%s/%s'", owner, repo)
        return await self._request_paged_json("GET", f"/repos/{owner}/{repo}/branches")

    async def get_content(self, owner: str, repo: str, ref: str, content_path: str) -> tuple[int, str]:
        url = f"http://raw.githubusercontent.com/{owner}/{repo}/{ref}/{content_path}"
        self._logger.debug("retrieving content for path '%s' in repo '%s/%s'", content_path, owner, repo)
        status, content = await self._request_raw("GET", url, refresh=False, headers=None)
        return status, content

    async def _request_paged_json(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        data: str | None = None,
    ) -> list[dict[str, Any]]:
        from urllib import parse

        result = []
        query_params: dict[str, str] | None = {"per_page": "100"}

        url = self._build_api_url(path)

        while query_params is not None:
            if params is not None:
                query_params.update(params)

            status, body, next_url = await self._request_raw_with_next_link(method, url, query_params, data)
            self._check_response(url, status, body)
            response = json.loads(body)

            if next_url is None:
                query_params = None
            else:
                query_params = {k: v[0] for k, v in parse.parse_qs(parse.urlparse(next_url).query).items()}

            for item in response:
                result.append(item)

        return result

    async def _request_json(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        data: str | None = None,
        refresh: bool = True,
        headers: Mapping[str, str] = _GH_HEADERS,
    ) -> dict[str, Any]:
        url = self._build_api_url(path)
        headers_with_auth = self._add_authorization_header(headers)
        status, content = await self._request_raw(method, url, params, data, refresh, headers_with_auth)
        self._check_response(url, status, content)
        return dict(json.loads(content))

    async def _request_raw_with_next_link(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: str | None = None,
        refresh: bool = True,
        headers: Mapping[str, str] = _GH_HEADERS,
    ) -> tuple[int, str, str | None]:
        self._logger.debug(
            "raw_with_links: '%s' url = %s, params = %s, data = %s, refresh = %d", method, url, params, data, refresh
        )

        headers_with_auth = self._add_authorization_header(headers)

        async with self._session.request(
            method,
            url=url,
            headers=headers_with_auth,
            params=params,
            data=data,
            refresh=refresh,
        ) as response:
            text = await response.text()
            status = response.status
            links = response.links
            next_link = links.get("next", None) if links is not None else None
            next_url = next_link.get("url", None) if next_link is not None else None
            self._logger.debug(
                "result\\[url=%s] = (%d, '%s', '%s')", url, status, "..." if status < 400 else text, next_url
            )
            return status, text, str(next_url) if next_url is not None else None

    async def _request_raw(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        data: str | None = None,
        refresh: bool = True,
        headers: Mapping[str, str] | None = None,
    ) -> tuple[int, str]:
        self._logger.debug(
            "raw: '%s' url = %s, params = %s, data = %s, refresh = %d", method, url, params, data, refresh
        )

        async with self._session.request(
            method, url=url, headers=headers, params=params, data=data, refresh=refresh
        ) as response:
            text = await response.text()
            status = response.status
            self._logger.debug("result\\[url=%s] = (%d, '%s')", url, status, "..." if status < 400 else text)
            return status, text

    @staticmethod
    def _check_response(url: str, status: int, body: str) -> None:
        if status >= 400:
            raise RuntimeError(f"failed to retrieve data from '{url}': ({status}, {body})")
