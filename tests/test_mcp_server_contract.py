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

"""
Contract test between the backend and the MCP server (``mcp-server/``).

The MCP server is a separate package with its own environment, so it cannot import backend enums.
It duplicates their values in a standard-library-only module, loaded here without installing the
MCP server: if a backend enum changes, this test fails and reminds to update the MCP server.
"""

import enum
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import get_args

import pytest

from antarest.study.business.model.config.general_model import Mode
from antarest.study.business.model.link_model import AssetType, TransmissionCapacity
from antarest.study.business.model.renewable_cluster_model import RenewableClusterGroup
from antarest.study.business.model.sts_model import STStorageGroup
from antarest.study.business.model.thermal_cluster_model import ThermalClusterGroup

MCP_ENUMS_PATH = Path(__file__).parents[1] / "mcp-server" / "src" / "antares_web_mcp" / "enums.py"


def _load_mcp_enums() -> ModuleType:
    spec = importlib.util.spec_from_file_location("antares_web_mcp_enums", MCP_ENUMS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "mcp_literal, backend_enum",
    [
        ("AssetTypeValue", AssetType),
        ("TransmissionCapacityValue", TransmissionCapacity),
        ("SimulationModeValue", Mode),
        ("ThermalGroupValue", ThermalClusterGroup),
        ("RenewableGroupValue", RenewableClusterGroup),
        ("StorageGroupValue", STStorageGroup),
    ],
)
def test_enums_are_in_sync_with_mcp_server(mcp_literal: str, backend_enum: type[enum.Enum]) -> None:
    mcp_values = set(get_args(getattr(_load_mcp_enums(), mcp_literal)))

    assert mcp_values == {e.value for e in backend_enum}, (
        f"Update `{mcp_literal}` in mcp-server/src/antares_web_mcp/enums.py"
    )
