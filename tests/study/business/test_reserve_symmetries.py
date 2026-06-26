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

import pytest

from antarest.study.business.model.thermal_reserve_symmetries_model import merge_symmetries


@pytest.mark.parametrize(
    "symmetries,merged_symmetries",
    [
        ([["a", "b"], ["c", "d"]], [["a", "b"], ["c", "d"]]),
        ([["a", "b"], ["a", "d"]], [["a", "b", "d"]]),
        ([["a", "b", "c"], ["c", "d"], ["e", "f"], ["b", "d"]], [["a", "b", "c", "d"], ["e", "f"]]),
    ],
)
def test_merge_symmetries(symmetries: list[list[str]], merged_symmetries: list[list[str]]) -> None:
    assert merge_symmetries(symmetries) == merged_symmetries
