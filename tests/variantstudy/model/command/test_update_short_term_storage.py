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

from antarest.core.serde.ini_reader import read_ini
from antarest.core.serde.ini_writer import write_ini_file
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.update_st_storages import UpdateSTStorages
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateRenewableCluster:
    def _set_up(self, study: FileStudy, command_context: CommandContext):
        CreateArea(area_name="FR", command_context=command_context, study_version=study.config.version).apply(study)
        CreateArea(area_name="de", command_context=command_context, study_version=study.config.version).apply(study)
        CreateSTStorage(
            area_id="fr",
            parameters={"name": "STORAGE_1"},
            command_context=command_context,
            study_version=study.config.version,
        ).apply(study)
        CreateSTStorage(
            area_id="fr",
            parameters={"name": "storage_2"},
            command_context=command_context,
            study_version=study.config.version,
        ).apply(study)
        CreateSTStorage(
            area_id="de",
            parameters={"name": "Storage_3??"},
            command_context=command_context,
            study_version=study.config.version,
        ).apply(study)

    def test_nominal_case(self, empty_study_870: FileStudy, command_context: CommandContext):
        study = empty_study_870
        self._set_up(study, command_context)
        study_version = study.config.version
        study_path = study.config.study_path

        # Check existing properties
        fr_ini = study_path / "input" / "st-storage" / "clusters" / "fr" / "list.ini"
        de_ini = study_path / "input" / "st-storage" / "clusters" / "de" / "list.ini"
        fr_content = read_ini(fr_ini)
        de_content = read_ini(de_ini)
        expected_fr_content = {
            "storage_1": {
                "efficiency": 1.0,
                "group": "other1",
                "initiallevel": 0.5,
                "initialleveloptim": False,
                "injectionnominalcapacity": 0.0,
                "name": "STORAGE_1",
                "reservoircapacity": 0.0,
                "withdrawalnominalcapacity": 0.0,
            },
            "storage_2": {
                "efficiency": 1.0,
                "group": "other1",
                "initiallevel": 0.5,
                "initialleveloptim": False,
                "injectionnominalcapacity": 0.0,
                "name": "storage_2",
                "reservoircapacity": 0.0,
                "withdrawalnominalcapacity": 0.0,
            },
        }
        assert fr_content == expected_fr_content
        expected_de_content = {
            "storage_3": {
                "efficiency": 1.0,
                "group": "other1",
                "initiallevel": 0.5,
                "initialleveloptim": False,
                "injectionnominalcapacity": 0.0,
                "name": "Storage_3??",
                "reservoircapacity": 0.0,
                "withdrawalnominalcapacity": 0.0,
            }
        }
        assert de_content == expected_de_content

        # Updates the ini file of DE to put the name as the key of the section
        expected_de_content["Storage_3??"] = expected_de_content.pop("storage_3")
        write_ini_file(de_ini, expected_de_content)

        # Update several properties
        new_properties = {"fr": {"storage_1": {"efficiency": 0.8}}, "DE": {"Storage_3": {"initial_level": 0.1}}}
        cmd = UpdateSTStorages(
            storage_properties=new_properties,
            command_context=command_context,
            study_version=study_version,
        )
        output = cmd.apply(study)
        assert output.status is True
        assert output.message == "The short-term storages were successfully updated."

        # Checks updated properties
        fr_content = read_ini(fr_ini)
        de_content = read_ini(de_ini)
        expected_fr_content["storage_1"]["efficiency"] = 0.8
        expected_de_content = {
            "Storage_3??": {
                "efficiency": 1.0,
                "group": "other1",
                "initiallevel": 0.1,
                "initialleveloptim": False,
                "injectionnominalcapacity": 0.0,
                "name": "Storage_3??",
                "reservoircapacity": 0.0,
                "withdrawalnominalcapacity": 0.0,
            }
        }
        assert fr_content == expected_fr_content
        assert de_content == expected_de_content

    def test_error_cases(self, empty_study_870: FileStudy, command_context: CommandContext):
        study = empty_study_870
        self._set_up(study, command_context)
        study_version = study.config.version

        # Fake area
        cmd = UpdateSTStorages(
            storage_properties={"fake_area": {"a": {"enabled": False}}},
            command_context=command_context,
            study_version=study_version,
        )
        output = cmd.apply(study)
        assert output.status is False
        assert output.message == "The area 'fake_area' is not found."

        # Fake cluster
        cmd = UpdateSTStorages(
            storage_properties={"FR": {"fake_storage": {"enabled": False}}},
            command_context=command_context,
            study_version=study_version,
        )
        output = cmd.apply(study)
        assert output.status is False
        assert output.message == "The short-term storage 'fake_storage' in the area 'fr' is not found."
