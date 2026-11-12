# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import json
from typing import Any

import httpx2

BASE_URL = "http://antares.test"


class FakeAntaresWeb:
    """
    In-memory stand-in for the Antares Web REST API, plugged into ``httpx2`` through a ``MockTransport``.

    Register canned responses with ``route()``; every received request is recorded in ``requests``.
    Several responses registered for the same route are returned in order (the last one is repeated),
    which simulates polling (e.g. a job "running" then "success"). Routes registered with ``params``
    only answer the requests with these query parameters (e.g. the ``path`` of the ``/raw`` endpoint).
    """

    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], list[httpx2.Response]] = {}
        self.param_routes: dict[tuple[str, str], list[tuple[dict[str, str], httpx2.Response]]] = {}
        self.requests: list[httpx2.Request] = []

    def route(
        self,
        method: str,
        path: str,
        *,
        status_code: int = 200,
        json_body: Any = None,
        text: str | None = None,
        content_type: str | None = None,
        params: dict[str, str] | None = None,
    ) -> None:
        if text is not None:
            headers = {"content-type": content_type} if content_type else None
            response = httpx2.Response(status_code, text=text, headers=headers)
        else:
            response = httpx2.Response(status_code, json=json_body)
        if params is not None:
            self.param_routes.setdefault((method, path), []).append((params, response))
        else:
            self.routes.setdefault((method, path), []).append(response)

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        key = (request.method, request.url.raw_path.decode().split("?")[0])
        for params, response in self.param_routes.get(key, []):
            if all(request.url.params.get(name) == value for name, value in params.items()):
                return response
        responses = self.routes.get(key)
        if not responses:
            return httpx2.Response(404, json={"description": f"no fake route for {request.url}", "exception": "Fake"})
        return responses.pop(0) if len(responses) > 1 else responses[0]

    @property
    def last_request(self) -> httpx2.Request:
        return self.requests[-1]

    def last_json(self) -> Any:
        return json.loads(self.last_request.content)

    def requests_to(self, method: str, path: str) -> list[httpx2.Request]:
        return [r for r in self.requests if r.method == method and r.url.raw_path.decode().split("?")[0] == path]

    def json_sent_to(self, method: str, path: str) -> list[Any]:
        return [json.loads(r.content) for r in self.requests_to(method, path)]
