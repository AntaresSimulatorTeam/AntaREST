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
import pytest
from pydantic import ValidationError

from antarest.study.business.model.hydro_model import InflowStructureUpdate
from antarest.study.dao.file.file_study_hydro_dao import get_inflow_path
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.update_inflow_structure import UpdateInflowStructure
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateInflowStructure:
    @staticmethod
    def _set_up(study: FileStudy, command_context: CommandContext):
        CreateArea(area_name="FR", command_context=command_context, study_version=study.config.version).apply(study)
        CreateArea(area_name="be", command_context=command_context, study_version=study.config.version).apply(study)

    def test_lifecycle(self, empty_study_880: FileStudy, command_context: CommandContext):
        """
        test inflow structure cannot have an inter_monthly_correlation lesser than 0 and greater than 1
        check status and message
        """
        study_version = empty_study_880.config.version
        self._set_up(empty_study_880, command_context)

        # check the initial hydro file
        inflow_file = empty_study_880.tree.get(get_inflow_path("fr"))
        assert inflow_file == {"intermonthly-correlation": 0.5}

        # test with invalid data
        # "inter-monthly correlation" must be between 0 and 1
        update_properties = {"inter_monthly_correlation": 22}
        with pytest.raises(ValidationError):
            InflowStructureUpdate(**update_properties)

        update_properties = {"inter_monthly_correlation": -2.0}
        with pytest.raises(ValidationError):
            InflowStructureUpdate(**update_properties)

        # test with valid data
        update_properties = {"inter_monthly_correlation": 0.8}
        inflow_structure_update = InflowStructureUpdate(**update_properties)
        command = UpdateInflowStructure(
            area_id="fr",
            command_context=command_context,
            study_version=study_version,
            properties=inflow_structure_update,
        )

        result = command.apply(empty_study_880)
        assert result.status
        assert result.message == "Inflow properties in 'fr' updated."

        # check the updated hydro file
        inflow_file = empty_study_880.tree.get(get_inflow_path("fr"))
        assert inflow_file == {"intermonthly-correlation": 0.8}
