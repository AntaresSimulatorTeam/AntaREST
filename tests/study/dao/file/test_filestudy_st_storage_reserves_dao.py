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

from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.business.model.reserve_certification_model import StorageReserveCertification
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.business.model.sts_model import STStorage
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import STUDY_VERSION_10_2
from antarest.study.storage.rawstudy.model.filesystem.config.reserve_participations import (
    parse_st_storage_reserves_certifications,
    parse_st_storage_reserves_symmetries,
)


def test_symmetries_and_certifications_do_not_overwrite_each_other(fs_dao: FileStudyTreeDao) -> None:
    # Build a v10.0 FS DAO.
    dao = fs_dao
    dao.get_file_study().config.version = STUDY_VERSION_10_2
    # Create 1 area with 2 short-term storages and 4 reserves
    dao.save_areas_with_properties({"fr": AreaProperties()})
    dao.save_st_storages({"fr": [STStorage(name="sts1", id="sts1"), STStorage(name="sts2", id="sts2")]})
    reserves = []
    for reserve_name in ["r1", "r2", "r3", "r4"]:
        reserves.append(ReserveDefinition(name=reserve_name, type=ReserveType.DOWN))
    dao.save_reserve_definitions({"fr": reserves})

    # A storage can only be symmetric on reserves it is certified for, so certify everything sts1 needs first.
    dao.save_st_storage_reserve_certifications(
        {
            "fr": {
                "r1": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
                "r2": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
                "r3": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
                "r4": {"sts1": StorageReserveCertification()},
            }
        }
    )

    # Save 2 symmetries. Then 1 certification. Ensures the certification writing didn't affect the symmetries.
    dao.save_st_storage_reserve_symmetries({"fr": {"sts1": [["r1", "r2"], ["r3", "r4"]]}})
    dao.save_st_storage_reserve_certifications(
        {
            "fr": {
                "r1": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
                "r2": {"sts2": StorageReserveCertification()},
                "r3": {"sts2": StorageReserveCertification()},
            }
        }
    )

    assert dao.get_st_storage_reserve_symmetries("fr") == {"sts1": [["r1", "r2"], ["r3", "r4"]]}
    assert dao.get_st_storage_reserve_certifications("fr") == {
        "r1": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
        "r2": {"sts2": StorageReserveCertification()},
        "r3": {"sts2": StorageReserveCertification()},
    }

    # Save a new symmetry. Ensures the symmetry writing didn't affect the certification.
    dao.save_st_storage_reserve_symmetries({"fr": {"sts2": [["r1", "r2", "r3"]]}})

    assert dao.get_st_storage_reserve_certifications("fr") == {
        "r1": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
        "r2": {"sts2": StorageReserveCertification()},
        "r3": {"sts2": StorageReserveCertification()},
    }
    # The symmetry should also be overwritten by the new value.
    assert dao.get_st_storage_reserve_symmetries("fr") == {"sts2": [["r1", "r2", "r3"]]}


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
