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
from pathlib import Path

from antarest.study.business.model.common import FilterOption
from antarest.study.business.model.link_model import AssetType, Link, LinkStyle, TransmissionCapacity
from antarest.study.business.model.xpansion_model import (
    Master,
    Solver,
    UcType,
    XpansionResourceFileType,
    XpansionSensitivitySettings,
    XpansionSettings,
)
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import with_admin_user
from tests.storage.integration.conftest import UUID


@with_admin_user
def test_convert_study(storage_service: StudyService, tmp_path: Path, command_context: CommandContext) -> None:
    """
    For the moment, it only ensures the method doesn't crash
    """
    source_path = tmp_path / "studies" / UUID
    new_path = tmp_path / "studies" / "new_study" / UUID
    storage_service.write_study_as_file_study(UUID, new_path)

    # Create DAO based on new study to test the study content.
    factory = storage_service.storage_service.raw_study_service.study_factory
    file_study = factory.create_from_fs(new_path, with_matrix_normalization=False, study_id="", use_cache=False)
    context = command_context
    file_study_dao = FileStudyTreeDao(file_study, context.generator_matrix_constants, context.blob_service)

    # Links
    assert file_study_dao.get_links() == [
        Link(
            area1="de",
            area2="fr",
            hurdles_cost=True,
            loop_flow=False,
            use_phase_shifter=False,
            transmission_capacities=TransmissionCapacity.ENABLED,
            asset_type=AssetType.AC,
            display_comments=True,
            comments="",
            colorr=112,
            colorb=112,
            colorg=112,
            link_width=1.0,
            link_style=LinkStyle.PLAIN,
            filter_synthesis=[],
            filter_year_by_year=[FilterOption.HOURLY],
        ),
        Link(
            area1="es",
            area2="fr",
            hurdles_cost=True,
            loop_flow=False,
            use_phase_shifter=False,
            transmission_capacities=TransmissionCapacity.ENABLED,
            asset_type=AssetType.AC,
            display_comments=True,
            comments="",
            colorr=112,
            colorb=112,
            colorg=112,
            link_width=1.0,
            link_style=LinkStyle.PLAIN,
            filter_synthesis=[],
            filter_year_by_year=[FilterOption.HOURLY],
        ),
        Link(
            area1="fr",
            area2="it",
            hurdles_cost=True,
            loop_flow=False,
            use_phase_shifter=False,
            transmission_capacities=TransmissionCapacity.ENABLED,
            asset_type=AssetType.AC,
            display_comments=True,
            comments="",
            colorr=112,
            colorb=112,
            colorg=112,
            link_width=1.0,
            link_style=LinkStyle.PLAIN,
            filter_synthesis=[],
            filter_year_by_year=[FilterOption.HOURLY],
        ),
    ]

    # Binding constraints
    assert file_study_dao.get_all_constraints() == {}
    # Settings

    # Thermal clusters

    # Renewable clusters
    # Short-term storages
    # Hydro

    # User folder
    assert list(file_study_dao.get_all_user_resources()) == []

    # Xpansion
    assert file_study_dao.get_xpansion_settings() == XpansionSettings(
        master=Master.RELAXED,
        uc_type=UcType.EXPANSION_FAST,
        optimality_gap=1000000.0,
        relative_gap=1e-06,
        relaxed_optimality_gap=1e-05,
        max_iteration=200,
        solver=Solver.XPRESS,
        log_level=1,
        separation_parameter=0.5,
        batch_size=96,
        yearly_weights="",
        additional_constraints="",
        timelimit=10000,
        sensitivity_config=XpansionSensitivitySettings(epsilon=0.0, projection=[], capex=False),
    )

    assert file_study_dao.get_all_xpansion_candidates() == []
    assert file_study_dao.get_xpansion_resources(XpansionResourceFileType.CONSTRAINTS) == []
    assert file_study_dao.get_xpansion_resources(XpansionResourceFileType.WEIGHTS) == []
    assert file_study_dao.get_xpansion_resources(XpansionResourceFileType.CAPACITIES) == []

    # Outputs
    outputs_before = [f.name for f in (source_path / "output").iterdir()]
    assert [f.name for f in (new_path / "output").iterdir()] == outputs_before
