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
Allowed values of some Antares Web fields, exposed to the model as JSON schema enums.

They mirror backend enums and are duplicated on purpose, to keep this package independent
from the backend. The backend test suite checks that they stay in sync
(``tests/test_mcp_server_contract.py`` at the root of the AntaREST repository).

This module must only depend on the standard library: the backend tests load it directly.
"""

from typing import Literal

AssetTypeValue = Literal["ac", "dc", "gaz", "virt", "other"]
"""Mirrors ``antarest.study.business.model.link_model.AssetType``."""

TransmissionCapacityValue = Literal["enabled", "ignore", "infinite"]
"""Mirrors ``antarest.study.business.model.link_model.TransmissionCapacity``."""

SimulationModeValue = Literal["Economy", "Adequacy", "Expansion"]
"""Mirrors ``antarest.study.business.model.config.general_model.Mode``."""

ThermalGroupValue = Literal[
    "nuclear", "lignite", "hard coal", "gas", "oil", "mixed fuel", "other 1", "other 2", "other 3", "other 4"
]
"""Mirrors ``antarest.study.business.model.thermal_cluster_model.ThermalClusterGroup``."""

RenewableGroupValue = Literal[
    "solar thermal",
    "solar pv",
    "solar rooftop",
    "wind onshore",
    "wind offshore",
    "other res 1",
    "other res 2",
    "other res 3",
    "other res 4",
]
"""Mirrors ``antarest.study.business.model.renewable_cluster_model.RenewableClusterGroup``."""

StorageGroupValue = Literal[
    "psp_open", "psp_closed", "pondage", "battery", "other1", "other2", "other3", "other4", "other5"
]
"""Mirrors ``antarest.study.business.model.sts_model.STStorageGroup``."""
