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
from checksumdir import dirhash
from pydantic import ValidationError

from antarest.core.serde.ini_reader import read_ini
from antarest.core.serde.ini_writer import write_ini_file
from antarest.study.business.model.sts_model import STStorageCreation
from antarest.study.model import STUDY_VERSION_8_8, STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.update_st_storages import UpdateSTStorages
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateShortTermSorage:
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

    def test_nominal_case(
        self, empty_study_880: FileStudy, empty_study_920: FileStudy, command_context: CommandContext
    ):
        for study in [empty_study_880, empty_study_920]:
            self._set_up(study, command_context)
            study_version = study.config.version
            study_path = study.config.study_path

            # Check existing `fr` properties
            fr_ini = study_path / "input" / "st-storage" / "clusters" / "fr" / "list.ini"
            fr_content = read_ini(fr_ini)
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
                    "enabled": True,
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
                    "enabled": True,
                },
            }
            if study_version == STUDY_VERSION_9_2:
                for storage in ["storage_1", "storage_2"]:
                    expected_fr_content[storage]["efficiencywithdrawal"] = 1
                    expected_fr_content[storage]["penalize-variation-injection"] = False
                    expected_fr_content[storage]["penalize-variation-withdrawal"] = False
            assert fr_content == expected_fr_content

            # Check existing `de` properties
            de_ini = study_path / "input" / "st-storage" / "clusters" / "de" / "list.ini"
            de_content = read_ini(de_ini)
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
                    "enabled": True,
                }
            }
            if study_version == STUDY_VERSION_9_2:
                expected_de_content["storage_3"]["efficiencywithdrawal"] = 1
                expected_de_content["storage_3"]["penalize-variation-injection"] = False
                expected_de_content["storage_3"]["penalize-variation-withdrawal"] = False
            assert de_content == expected_de_content

            # Updates the ini file of DE to put the name as the key of the section
            expected_de_content["Storage_3??"] = expected_de_content.pop("storage_3")
            write_ini_file(de_ini, expected_de_content)

            # Update several properties
            new_properties = {"fr": {"storage_1": {"efficiency": 0.3}}, "DE": {"Storage_3": {"initial_level": 0.1}}}
            if study_version >= STUDY_VERSION_9_2:
                new_properties["fr"]["storage_1"]["efficiency_withdrawal"] = 0.8
                new_properties["DE"]["Storage_3"]["penalize_variation_injection"] = True
                new_properties["DE"]["Storage_3"]["group"] = "MY DESIGN !!!"
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
            expected_fr_content["storage_1"]["efficiency"] = 0.3
            if study_version >= STUDY_VERSION_9_2:
                expected_fr_content["storage_1"]["efficiencywithdrawal"] = 0.8
            assert fr_content == expected_fr_content

            de_content = read_ini(de_ini)
            expected_de_content = {
                "storage_3": {
                    "efficiency": 1.0,
                    "group": "other1",
                    "initiallevel": 0.1,
                    "initialleveloptim": False,
                    "injectionnominalcapacity": 0.0,
                    "name": "Storage_3??",
                    "reservoircapacity": 0.0,
                    "withdrawalnominalcapacity": 0.0,
                    "enabled": True,
                }
            }
            if study_version >= STUDY_VERSION_9_2:
                expected_de_content["storage_3"]["efficiencywithdrawal"] = 1
                expected_de_content["storage_3"]["penalize-variation-withdrawal"] = False
                expected_de_content["storage_3"]["penalize-variation-injection"] = True
                expected_de_content["storage_3"]["group"] = "my design !!!"  # allowed and written in lower case
            assert de_content == expected_de_content

    def test_error_cases(self, empty_study_880: FileStudy, command_context: CommandContext):
        study = empty_study_880
        self._set_up(study, command_context)
        study_version = study.config.version

        # Create a short-term storage
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="fr",
            parameters=STStorageCreation(**{"name": "sts_1"}),
            study_version=STUDY_VERSION_8_8,
        )
        output = cmd.apply(study)
        assert output.status is True

        # Fake area
        cmd = UpdateSTStorages(
            storage_properties={"fake_area": {"a": {"initial_level": 0.4}}},
            command_context=command_context,
            study_version=study_version,
        )
        output = cmd.apply(study)
        assert output.status is False
        assert output.message == "The area 'fake_area' is not found."

        # Ensures updating an unexisting short-term storage raises an Exception.
        # Also ensures the study wasn't partially modified.
        hash_before_update = dirhash(study.config.study_path / "input" / "st-storage", "md5")
        mapping = {"de": {"storage_3": {"enabled": False}}, "FR": {"fake_storage": {"initial_level": 0.1}}}
        cmd = UpdateSTStorages(
            storage_properties=mapping,
            command_context=command_context,
            study_version=study_version,
        )
        output = cmd.apply(study)
        assert output.status is False
        assert output.message == "The short-term storage 'fake_storage' in the area 'fr' is not found."
        hash_after_update = dirhash(study.config.study_path / "input" / "st-storage", "md5")
        assert hash_before_update == hash_after_update

        # Try to give a parameter that only exist since v9.2
        with pytest.raises(
            ValidationError,
            match="Field efficiency_withdrawal is not a valid field for study version 8.8",
        ):
            UpdateSTStorages(
                storage_properties={"fr": {"storage_1": {"efficiencyWithdrawal": 0.8}}},
                command_context=command_context,
                study_version=study_version,
            )
