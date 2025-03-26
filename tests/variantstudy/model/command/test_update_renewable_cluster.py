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

from antarest.core.serde.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command.update_renewables_clusters import UpdateRenewablesClusters
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateRenewableCluster:
    def _set_up(self, study: FileStudy, command_context: CommandContext):
        CreateArea(area_name="FR", command_context=command_context, study_version=study.config.version).apply(study)
        CreateArea(area_name="de", command_context=command_context, study_version=study.config.version).apply(study)
        # Modify the general data to put the sutdy in mode clusters
        UpdateConfig(
            target="settings/generaldata/other preferences/renewable-generation-modelling",
            data="clusters",
            command_context=command_context,
            study_version=study.config.version,
        ).apply(study)
        CreateRenewablesCluster(
            area_id="fr",
            parameters={"name": "CLUSTER_1"},
            command_context=command_context,
            study_version=study.config.version,
        ).apply(study)
        CreateRenewablesCluster(
            area_id="fr",
            parameters={"name": "cluster_2"},
            command_context=command_context,
            study_version=study.config.version,
        ).apply(study)
        CreateRenewablesCluster(
            area_id="de",
            parameters={"name": "Cluster_3"},
            command_context=command_context,
            study_version=study.config.version,
        ).apply(study)

    def test_nominal_case(self, empty_study_870: FileStudy, command_context: CommandContext):
        study = empty_study_870
        self._set_up(study, command_context)
        study_version = study.config.version
        study_path = study.config.study_path

        # Check existing properties
        fr_ini = study_path / "input" / "renewables" / "clusters" / "fr" / "list.ini"
        de_ini = study_path / "input" / "renewables" / "clusters" / "de" / "list.ini"
        fr_content = IniReader().read(fr_ini)
        de_content = IniReader().read(de_ini)
        expected_fr_content = {
            "CLUSTER_1": {
                "name": "CLUSTER_1",
                "enabled": True,
                "unitcount": 1,
                "nominalcapacity": 0.0,
                "group": "other res 1",
                "ts-interpretation": "power-generation",
            },
            "cluster_2": {
                "name": "cluster_2",
                "enabled": True,
                "unitcount": 1,
                "nominalcapacity": 0.0,
                "group": "other res 1",
                "ts-interpretation": "power-generation",
            },
        }
        assert fr_content == expected_fr_content
        expected_de_content = {
            "Cluster_3": {
                "name": "Cluster_3",
                "enabled": True,
                "unitcount": 1,
                "nominalcapacity": 0.0,
                "group": "other res 1",
                "ts-interpretation": "power-generation",
            }
        }
        assert de_content == expected_de_content

        # Update several properties
        new_properties = {"fr": {"cluster_1": {"enabled": False}}, "DE": {"CLUSTER_3": {"unit_count": 4}}}
        cmd = UpdateRenewablesClusters(
            cluster_properties=new_properties,
            command_context=command_context,
            study_version=study_version,
        )
        output = cmd.apply(study)
        assert output.status is True
        assert output.message == "The renewable clusters were successfully updated."

        # Checks updated properties
        fr_content = IniReader().read(fr_ini)
        de_content = IniReader().read(de_ini)
        expected_fr_content["CLUSTER_1"]["enabled"] = False
        expected_de_content["Cluster_3"]["unitcount"] = 4
        assert fr_content == expected_fr_content
        assert de_content == expected_de_content

    def test_error_cases(self, empty_study_880: FileStudy, command_context: CommandContext):
        study = empty_study_880
        self._set_up(study, command_context)
        study_version = study.config.version

        # Fake area
        cmd = UpdateRenewablesClusters(
            cluster_properties={"fake_area": {"a": {"enabled": False}}},
            command_context=command_context,
            study_version=study_version,
        )
        output = cmd.apply(study)
        assert output.status is False
        assert output.message == "The area 'fake_area' is not found."

        # Fake cluster
        cmd = UpdateRenewablesClusters(
            cluster_properties={"FR": {"fake_cluster": {"enabled": False}}},
            command_context=command_context,
            study_version=study_version,
        )
        output = cmd.apply(study)
        assert output.status is False
        assert output.message == "The renewable cluster 'fake_cluster' in the area 'fr' is not found."
