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

from antarest.study.business.model.reserve_certification_model import ThermalReserveCertification
from antarest.study.storage.rawstudy.model.filesystem.config.reserve_participations import (
    parse_thermal_reserves_certifications,
    parse_thermal_reserves_symmetries,
    serialize_thermal_reserve_participations,
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
    with pytest.raises(ValueError, match="Some reserves are duplicated for th1"):
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


def test_a_collapsed_symmetry_is_dropped_instead_of_written_as_an_empty_list() -> None:
    symmetries = {"th1": [["r1", "r2"]]}
    certifications = {"r2": {"th1": ThermalReserveCertification(max_power=1.0)}}

    # "r1" is not certified anymore, so the symmetry is left with a single reserve,
    # this it's removed as there's no such thing as symmetries with a single reserve.
    content = serialize_thermal_reserve_participations(symmetries, certifications)

    assert content == {
        "participations": [
            {
                "cluster": "th1",
                "certifications": [
                    {
                        "reserve": "r2",
                        "max-power": 1.0,
                        "max-power-off": 0.0,
                        "participation-cost": 0.0,
                        "participation-cost-off": 0.0,
                    }
                ],
            }
        ]
    }
    # The file must stay readable: an absent key parses back as "no symmetry".
    assert parse_thermal_reserves_symmetries(content) == {}


def test_a_surviving_symmetry_is_still_written() -> None:
    symmetries = {"th1": [["r1", "r2"]]}
    certification = ThermalReserveCertification()

    content = serialize_thermal_reserve_participations(
        symmetries, {"r1": {"th1": certification}, "r2": {"th1": certification}}
    )

    assert content["participations"][0]["symmetries"] == [{"reserves": ["r1", "r2"]}]
    assert parse_thermal_reserves_symmetries(content) == symmetries
