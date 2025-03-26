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


from antarest.study.business.model.area_properties_model import (
    AreaPropertiesUpdate,
    get_adequacy_patch_path,
    get_optimization_path,
    get_thermal_path,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.update_areas_properties import UpdateAreasProperties
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def test_update_areas_properties(empty_study_870: FileStudy, command_context: CommandContext):
    empty_study = empty_study_870
    area_id = "area_test"
    CreateArea(area_name=area_id, command_context=command_context, study_version=empty_study.config.version).apply(
        empty_study
    )

    expected_thermal_props = {"spilledenergycost": {"area_test": 0.0}, "unserverdenergycost": {"area_test": 0.0}}
    expected_optimization_props = {
        "filtering": {
            "filter-synthesis": "hourly, daily, weekly, monthly, annual",
            "filter-year-by-year": "hourly, daily, weekly, monthly, annual",
        },
        "nodal optimization": {
            "dispatchable-hydro-power": True,
            "non-dispatchable-power": True,
            "other-dispatchable-power": True,
            "spread-spilled-energy-cost": 0.0,
            "spread-unsupplied-energy-cost": 0.0,
        },
    }
    expected_adequacy_props = {"adequacy-patch": {"adequacy-patch-mode": "outside"}}

    assert expected_thermal_props == empty_study.tree.get(get_thermal_path())
    assert expected_optimization_props == empty_study.tree.get(get_optimization_path(area_id))
    assert expected_adequacy_props == empty_study.tree.get(get_adequacy_patch_path(area_id))

    update_args = {
        "averageUnsuppliedEnergyCost": 2.0,
        "averageSpilledEnergyCost": 3.0,
        "nonDispatchablePower": False,
        "dispatchableHydroPower": False,
        "otherDispatchablePower": False,
        "spreadUnsuppliedEnergyCost": 4.0,
        "spreadSpilledEnergyCost": 5.0,
        "filterSynthesis": {"hourly"},
        "filterByYear": {"monthly", "annual"},
        "adequacyPatchMode": "inside",
    }

    update_area = AreaPropertiesUpdate(**update_args)

    UpdateAreasProperties(
        properties={area_id: update_area}, command_context=command_context, study_version=empty_study.config.version
    ).apply(empty_study)

    new_thermal_props = {"spilledenergycost": {"area_test": 3.0}, "unserverdenergycost": {"area_test": 2.0}}
    new_optimization_props = {
        "filtering": {"filter-synthesis": "hourly", "filter-year-by-year": "monthly, annual"},
        "nodal optimization": {
            "dispatchable-hydro-power": False,
            "non-dispatchable-power": False,
            "other-dispatchable-power": False,
            "spread-spilled-energy-cost": 5.0,
            "spread-unsupplied-energy-cost": 4.0,
        },
    }
    new_adequacy_props = {"adequacy-patch": {"adequacy-patch-mode": "inside"}}

    assert new_thermal_props == empty_study.tree.get(get_thermal_path())
    assert new_optimization_props == empty_study.tree.get(get_optimization_path(area_id))
    assert new_adequacy_props == empty_study.tree.get(get_adequacy_patch_path(area_id))
