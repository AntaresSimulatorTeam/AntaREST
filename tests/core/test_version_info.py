# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from unittest.mock import patch

import pytest

from antarest.core.version_info import get_commit_id


class TestVersionInfo:
    @pytest.mark.unit_test
    def test_get_commit_id__commit_id__exist(self, tmp_path) -> None:
        path_commit_id = tmp_path.joinpath("commit_id")
        path_commit_id.write_text("6d891aba6e4a1c3a6f43b8ca00b021a20d319091")
        assert get_commit_id(tmp_path) == "6d891aba6e4a1c3a6f43b8ca00b021a20d319091"

    @pytest.mark.unit_test
    def test_get_commit_id__git_call_ok(self, tmp_path) -> None:
        actual = get_commit_id(tmp_path)
        assert re.fullmatch(r"[0-9a-fA-F]{40}", actual)

    @pytest.mark.unit_test
    def test_get_commit_id__git_call_failed(self, tmp_path) -> None:
        with patch("subprocess.check_output", side_effect=FileNotFoundError):
            assert not get_commit_id(tmp_path)
