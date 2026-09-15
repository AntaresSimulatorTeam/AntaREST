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
import shutil
from pathlib import Path

from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def test_default_case(dao_10_2: StudyDao) -> None:
    # We should not have a library for default studies
    library = dao_10_2.get_library()
    assert library is None


def _checks_library_integrity(library: GemsLibrary) -> None:
    # Metadata
    assert library is not None
    assert library.id == "andromede-v1-models-weo-hybrid"
    assert (
        library.description
        == "Andromede V1 model library - without expectation operators - allows hybrid connections (i.e. connections between Andromede models and Antares legacy area)"
    )
    assert library.version is None
    # Port types
    assert len(library.port_types) == 1
    port_type = library.port_types[0]
    assert port_type.id == "flow"
    assert port_type.description == "A port which transfers power flow"
    assert len(port_type.fields) == 1
    assert port_type.fields[0].id == "flow"
    assert port_type.thermal_capacity_connection is None
    assert port_type.area_connection is not None
    assert port_type.area_connection.spillage_bound is None
    assert port_type.area_connection.injection_to_balance == "flow"
    assert port_type.area_connection.unsupplied_energy_bound is None
    # Models
    assert len(library.models) == 2
    first_model = library.models[0]
    assert first_model.id == "dsr"
    assert first_model.description is None
    assert first_model.taxonomy_category is None
    assert first_model.properties == []
    assert len(first_model.parameters) == 2
    assert first_model.parameters[0].id == "max_load"
    assert first_model.parameters[0].time_dependent is True
    assert first_model.parameters[0].scenario_dependent is True
    assert first_model.parameters[1].id == "curtailment_price"
    assert first_model.parameters[1].time_dependent is False
    assert first_model.parameters[1].scenario_dependent is False
    assert len(first_model.ports) == 1
    assert first_model.ports[0].id == "balance_port"
    assert first_model.ports[0].type == "flow"
    second_model = library.models[1]
    assert second_model.id == "electrolyser"
    assert second_model.description is None
    assert second_model.taxonomy_category is None
    assert second_model.properties == []
    assert len(second_model.parameters) == 2
    assert second_model.parameters[0].id == "efficiency"
    assert second_model.parameters[0].time_dependent is False
    assert second_model.parameters[0].scenario_dependent is False
    assert second_model.parameters[1].id == "p_max"
    assert second_model.parameters[1].time_dependent is True
    assert second_model.parameters[1].scenario_dependent is True
    assert len(second_model.ports) == 2
    assert second_model.ports[0].id == "power_port"
    assert second_model.ports[0].type == "flow"
    assert second_model.ports[1].id == "hydrogen_port"
    assert second_model.ports[1].type == "flow"


def test_library_roundtrip(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    lib_folder = dao.get_file_study().config.study_path / "input" / "model-libraries"
    lib_folder.mkdir(exist_ok=True)
    shutil.copy(ASSETS_PATH / "gems" / "libraries" / "8_1_simulator_nr_tests.yml", lib_folder / "my_library.yml")

    library = dao.get_library()
    assert library is not None
    _checks_library_integrity(library)

    # Remove the library file
    (lib_folder / "my_library.yml").unlink()
    assert dao.get_library() is None

    # Save the old content
    dao.save_library(library)
    library = dao.get_library()
    assert library is not None
    _checks_library_integrity(library)
