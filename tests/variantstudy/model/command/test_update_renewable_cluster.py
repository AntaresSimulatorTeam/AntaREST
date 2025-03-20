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
from study.storage.rawstudy.model.filesystem.factory import FileStudy
from study.storage.variantstudy.model.command.create_area import CreateArea
from study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from study.storage.variantstudy.model.command.update_config import UpdateConfig
from study.storage.variantstudy.model.command.update_renewables_clusters import UpdateRenewablesClusters
from study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateRenewableCluster:
    def _set_up(self, study: FileStudy, command_context: CommandContext):
        CreateArea(area_name="FR", command_context=command_context, study_version=study.config.version).apply(study)
        # Modify the general data to put the sutdy in mode clusters
        UpdateConfig(
            target="settings/generaldata/other preferences/renewable-generation-modelling",
            data="clusters",
            command_context=command_context,
            study_version=study.config.version,
        ).apply(study)
        CreateRenewablesCluster(
            area_id="fr",
            parameters={"name": "CLUSTER"},
            command_context=command_context,
            study_version=study.config.version,
        ).apply(study)

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_nominal_case(self, empty_study: FileStudy, command_context: CommandContext):
        self._set_up(empty_study, command_context)

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_error_cases(self, empty_study: FileStudy, command_context: CommandContext):
        self._set_up(empty_study, command_context)
        study_version = empty_study.config.version

        # Fake area
        cmd = UpdateRenewablesClusters(
            cluster_properties={"fake_area": {"a": {"enabled": False}}},
            command_context=command_context,
            study_version=study_version,
        )
        output = cmd.apply(empty_study)
        assert output.status is False
        assert output.message == "The area 'fake_area' is not found."

        # Fake cluster
        cmd = UpdateRenewablesClusters(
            cluster_properties={"FR": {"fake_cluster": {"enabled": False}}},
            command_context=command_context,
            study_version=study_version,
        )
        output = cmd.apply(empty_study)
        assert output.status is False
        assert output.message == "The renewable cluster 'fake_cluster' in the area 'fr' is not found."
