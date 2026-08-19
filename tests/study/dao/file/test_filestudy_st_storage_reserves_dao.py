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

from antarest.study.storage.rawstudy.model.filesystem.config.reserve_participations import (
    parse_st_storage_reserves_certifications,
    parse_st_storage_reserves_symmetries,
)


def test_parsing_errors() -> None:
    # Duplicated short-term storages
    content = {
        "storage": "sts1",
        "symmetries": [{"reserves": ["r1", "r2", "r3", "r4"]}],
        "certifications": [{"reserve": "r1"}],
    }
    duplicated_content = {"participations": [content, content]}

    with pytest.raises(ValueError, match="Some short-term storages are duplicated"):
        parse_st_storage_reserves_certifications(duplicated_content)

    with pytest.raises(ValueError, match="Some short-term storages are duplicated"):
        parse_st_storage_reserves_symmetries(duplicated_content)

    # Duplicated reserve
    content = {
        "storage": "sts1",
        "symmetries": [{"reserves": ["r1", "r2"]}],
        "certifications": [{"reserve": "r1"}, {"reserve": "r1"}],
    }
    with pytest.raises(ValueError, match="Some reserves are duplicated for sts1"):
        parse_st_storage_reserves_certifications({"participations": [content]})

    # One symmetry only
    content = {
        "storage": "sts1",
        "symmetries": [{"reserves": ["r1"]}],
    }
    with pytest.raises(
        ValueError, match=re.escape("Reserve symmetries should have at least 2 elements, and was ['r1']")
    ):
        parse_st_storage_reserves_symmetries({"participations": [content]})

    # Duplicated reserve in symmetry
    content = {
        "storage": "sts1",
        "symmetries": [{"reserves": ["r1", "r1"]}],
    }
    with pytest.raises(ValueError, match="Reserve symmetries should not contain duplicates"):
        parse_st_storage_reserves_symmetries({"participations": [content]})
