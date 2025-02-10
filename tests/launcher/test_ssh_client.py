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

import math
from unittest.mock import Mock

import pytest

from antarest.launcher.ssh_client import SlurmError, calculates_slurm_load, parse_cpu_load, parse_cpu_used


@pytest.mark.unit_test
def test_parse_cpu_used() -> None:
    assert parse_cpu_used("3/28/1/32") == 100 * 3 / (3 + 28)


@pytest.mark.unit_test
def test_parse_cpu_load() -> None:
    sinfo_output = "0.01     24    \n0.01   24  \nN/A     24    \n9.94   24 "
    assert math.isclose(
        parse_cpu_load(sinfo_output),
        100 * (0.01 + 0.01 + 9.94) / (24 + 24 + 24),
    )


@pytest.mark.unit_test
def test_calculates_slurm_load_without_private_key_fails() -> None:
    ssh_config = Mock()
    with pytest.raises(SlurmError):
        calculates_slurm_load(ssh_config, "fake_partition")
