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

import re
from typing import Any
from unittest.mock import Mock

from fastapi import FastAPI
from starlette.testclient import TestClient
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.core_blueprint import create_utils_routes


class RegEx:
    """A helper object that compares equal to a regex."""

    def __init__(self, regex: str) -> None:
        self.regex = regex
        self.match = re.compile(self.regex).fullmatch

    @override
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, str) and self.match(other)

    @override
    def __ne__(self, other: Any) -> bool:
        return not isinstance(other, str) or not self.match(other)

    @override
    def __repr__(self) -> str:
        return f"<RegEx({self.regex!r})>"


class TestVersionInfo:
    def test_version_info(self, app: FastAPI) -> None:
        app.include_router(create_utils_routes(Config(), Mock()))
        client = TestClient(app, raise_server_exceptions=False)
        res = client.get("/version")
        res.raise_for_status()
        actual = res.json()
        expected = {
            "name": "AntaREST",
            "version": RegEx(r"\d+(?:\.\d+)+"),
            "gitcommit": RegEx(r"^[0-9a-fA-F]{40}$"),
            "dependencies": {},
        }
        assert actual == expected

        res = client.get("/version?with_deps=true")
        res.raise_for_status()
        actual = res.json()
        assert actual["dependencies"] != {}
