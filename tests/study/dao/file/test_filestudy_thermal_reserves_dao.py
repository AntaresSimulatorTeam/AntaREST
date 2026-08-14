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

import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.thermal_reserve_participations import (
    parse_thermal_reserves_certifications,
    parse_thermal_reserves_symmetries,
)


def test_parsing_errors() -> None:
    # Duplicated thermals
    content = {
        "cluster": "th1",
        "symmetries": [{"reserves": ["r1", "r2", "r3", "r4"]}],
        "certifications": [{"reserve": "r1"}],
    }
    duplicated_content = {"participations": [content, content]}

    with pytest.raises(ValueError, match="Some thermals are duplicated"):
        parse_thermal_reserves_certifications(duplicated_content)

    with pytest.raises(ValueError, match="Some thermals are duplicated"):
        parse_thermal_reserves_symmetries(duplicated_content)

    # Duplicated reserve
    content = {
        "cluster": "th1",
        "symmetries": [{"reserves": ["r1", "r2"]}],
        "certifications": [{"reserve": "r1"}, {"reserve": "r1"}],
    }
    with pytest.raises(ValueError, match="Some reserves are duplicated for cluster th1"):
        parse_thermal_reserves_certifications({"participations": [content]})

    # One symmetry only
    content = {
        "cluster": "th1",
        "symmetries": [{"reserves": ["r1"]}],
    }
    with pytest.raises(
        ValueError, match=re.escape("Reserve symmetries should have at least 2 elements, and was ['r1']")
    ):
        parse_thermal_reserves_symmetries({"participations": [content]})

    # Duplicated reserve in symmetry
    content = {
        "cluster": "th1",
        "symmetries": [{"reserves": ["r1", "r1"]}],
    }
    with pytest.raises(ValueError, match="Reserve symmetries should not contain duplicates"):
        parse_thermal_reserves_symmetries({"participations": [content]})
