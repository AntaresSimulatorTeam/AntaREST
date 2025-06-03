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
import copy
import re

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from antarest.core.serde.ini_reader import read_ini
from antarest.study.business.model.sts_model import STStorageCreation, STStorageGroup
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8, STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.model import CommandDTO

GEN = np.random.default_rng(1000)


# The parameter names to be used are those in the INI file.
# Non-string values are automatically converted into strings.
# noinspection SpellCheckingInspection
PARAMETERS = {
    "name": "Storage1",
    "group": "Battery",
    "injectionNominalCapacity": 1500,
    "withdrawalNominalCapacity": 1500,
    "reservoirCapacity": 20000,
    "efficiency": 0.94,
    "initialLevelOptim": True,
}

# noinspection SpellCheckingInspection
OTHER_PARAMETERS = {
    "name": "Storage1",
    "group": "Battery",
    "injectionNominalCapacity": 1200,
    "withdrawalNominalCapacity": 1300,
    "reservoirCapacity": 20500,
    "efficiency": 0.92,
    "initialLevel": 0,
    "initialLevelOptim": True,
}


class TestCreateSTStorage:
    # noinspection SpellCheckingInspection
    def test_init(self, command_context: CommandContext):
        pmax_injection = GEN.random((8760, 1))
        inflows = GEN.uniform(0, 1000, size=(8760, 1))
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageCreation(**PARAMETERS),
            pmax_injection=pmax_injection.tolist(),  # type: ignore
            inflows=inflows.tolist(),  # type: ignore
            study_version=STUDY_VERSION_8_6,
        )

        # Check the attribues
        assert cmd.command_name == CommandName.CREATE_ST_STORAGE
        assert cmd.study_version == STUDY_VERSION_8_6
        assert cmd.command_context == command_context
        assert cmd.area_id == "area_fr"
        expected_parameters = {k: str(v) for k, v in PARAMETERS.items()}
        assert cmd.parameters == STStorageCreation(**expected_parameters)

        # check the matrices links

        constants = command_context.generator_matrix_constants
        assert cmd.pmax_injection != constants.get_st_storage_pmax_injection()
        assert cmd.pmax_withdrawal == constants.get_st_storage_pmax_withdrawal()
        assert cmd.lower_rule_curve == constants.get_st_storage_lower_rule_curve()
        assert cmd.upper_rule_curve == constants.get_st_storage_upper_rule_curve()
        assert cmd.inflows != constants.get_st_storage_inflows()

    @pytest.mark.parametrize("group", ["Battery", "battery"])
    def test_init__lower_and_upper_case_groups_are_valid(self, command_context: CommandContext, group: str):
        params = copy.deepcopy(PARAMETERS)
        params["group"] = group
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageCreation(**PARAMETERS),
            study_version=STUDY_VERSION_8_8,
        )
        assert cmd.parameters.group == STStorageGroup.BATTERY.value

    def test_init__invalid_storage_name(self, empty_study_860: FileStudy, command_context: CommandContext):
        # When we apply the config for a new ST Storage with a bad name
        with pytest.raises(ValidationError) as ctx:
            parameters = {**PARAMETERS, "name": "?%$$"}  # bad name
            CreateSTStorage(
                command_context=command_context,
                area_id="dummy",
                parameters=STStorageCreation(**parameters),
                study_version=STUDY_VERSION_8_8,
            )
        # We get 2 errors because the `storage_name` is duplicated in the `parameters`:
        assert ctx.value.error_count() == 1
        raised_error = ctx.value.errors()[0]
        assert raised_error["type"] == "value_error"
        assert raised_error["msg"] == "Value error, Invalid name '?%$$'."
        assert raised_error["input"] == "?%$$"

    def test_init__invalid_matrix_values(self, command_context: CommandContext):
        array = GEN.random((8760, 1))
        array[10] = 25  # BAD
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageCreation(**PARAMETERS),
                pmax_injection=array.tolist(),  # type: ignore
                study_version=STUDY_VERSION_8_8,
            )
        assert ctx.value.error_count() == 1
        raised_error = ctx.value.errors()[0]
        assert raised_error["type"] == "value_error"
        assert raised_error["msg"] == "Value error, Matrix values should be between 0 and 1"
        assert "pmax_injection" in raised_error["input"]

    # noinspection SpellCheckingInspection
    def test_init__invalid_matrix_shape(self, command_context: CommandContext):
        array = GEN.random((24, 1))  # BAD SHAPE
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageCreation(**PARAMETERS),
                pmax_injection=array.tolist(),  # type: ignore
                study_version=STUDY_VERSION_8_8,
            )
        assert ctx.value.error_count() == 1
        raised_error = ctx.value.errors()[0]
        assert raised_error["type"] == "value_error"
        assert raised_error["msg"] == "Value error, Invalid matrix shape (24, 1), expected (8760, 1)"
        assert "pmax_injection" in raised_error["input"]

    def test_init__invalid_nan_value(self, command_context: CommandContext):
        array = GEN.random((8760, 1))  # OK
        array[20] = np.nan  # BAD
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageCreation(**PARAMETERS),
                pmax_injection=array.tolist(),  # type: ignore
                study_version=STUDY_VERSION_8_8,
            )
        assert ctx.value.error_count() == 1
        raised_error = ctx.value.errors()[0]
        assert raised_error["type"] == "value_error"
        assert raised_error["msg"] == "Value error, Matrix values cannot contain NaN"
        assert "pmax_injection" in raised_error["input"]

    def test_init__invalid_matrix_format(self, command_context: CommandContext):
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageCreation(**PARAMETERS),
                pmax_injection=[[1], [2], [3]],
                study_version=STUDY_VERSION_8_8,
            )
        assert ctx.value.error_count() == 1
        raised_error = ctx.value.errors()[0]
        assert raised_error["type"] == "value_error"
        assert raised_error["msg"] == "Value error, Invalid matrix shape (3, 1), expected (8760, 1)"
        assert "pmax_injection" in raised_error["input"]

    def test_init__invalid_matrix_for_version(self, command_context: CommandContext):
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageCreation(**PARAMETERS),
                cost_injection=[[1], [2], [3]],
                study_version=STUDY_VERSION_8_8,
            )
        assert ctx.value.error_count() == 1
        raised_error = ctx.value.errors()[0]
        assert raised_error["type"] == "value_error"
        assert raised_error["msg"] == (
            "Value error, You gave a 9.2 matrix: 'cost_injection' for a study in version 8.8"
        )
        assert "cost_injection" in raised_error["input"]

    def test_init__invalid_parameters_for_version(self, command_context: CommandContext):
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters={"name": "test", "efficiency_withdrawal": 0.45},
                study_version=STUDY_VERSION_8_8,
            )
        assert ctx.value.error_count() == 1
        raised_error = ctx.value.errors()[0]
        assert raised_error["type"] == "extra_forbidden"
        assert raised_error["msg"] == "Extra inputs are not permitted"
        assert "efficiency_withdrawal" in raised_error["loc"]

    def test_apply__invalid_version(self, empty_study_720: FileStudy, command_context: CommandContext):
        empty_study = empty_study_720
        # Given an old study in version 720
        # When we apply the config to add a new ST Storage
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="foo",
                parameters=STStorageCreation(**PARAMETERS),
                study_version=empty_study.config.version,
            )
        assert ctx.value.error_count() == 1
        raised_error = ctx.value.errors()[0]
        assert raised_error["type"] == "value_error"
        assert raised_error["msg"] == "Value error, Unsupported study version: 7.2"

    def test_apply__missing_area(self, empty_study_860: FileStudy, command_context: CommandContext):
        # Given a study without "unknown area" area
        # When we apply the config to add a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id="unknown area",  # bad ID
            parameters=STStorageCreation(**PARAMETERS),
            study_version=empty_study_860.config.version,
        )
        command_output = create_st_storage.apply(empty_study_860)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"'{re.escape(create_st_storage.area_id)}'.*does not exist",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply__duplicate_storage(self, empty_study_860: FileStudy, command_context: CommandContext):
        recent_study = empty_study_860
        # First, prepare a new Area
        create_area = CreateArea(
            area_name="Area FR", command_context=command_context, study_version=recent_study.config.version
        )
        create_area.apply(recent_study)

        # Then, apply the config for a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageCreation(**PARAMETERS),
            study_version=recent_study.config.version,
        )
        command_output = create_st_storage.apply(recent_study)
        assert command_output.status is True

        # Then, apply the config a second time
        parameters = {**PARAMETERS, "name": "STORAGE1"}  # different case
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageCreation(**parameters),
            study_version=recent_study.config.version,
        )
        command_output = create_st_storage.apply(recent_study)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"'{re.escape(create_st_storage.storage_name)}'.*already exists",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_create__nominal_case(self, empty_study_860: FileStudy, command_context: CommandContext):
        recent_study = empty_study_860
        # First, prepare a new Area
        create_area = CreateArea(
            area_name="Area FR", command_context=command_context, study_version=recent_study.config.version
        )
        create_area.apply(recent_study)

        # Then, apply the config for a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageCreation(**PARAMETERS),
            study_version=recent_study.config.version,
        )
        command_output = create_st_storage.apply(recent_study)

        # Check the command output and extra dict
        assert command_output.status is True
        assert re.search(
            rf"'{re.escape(create_st_storage.storage_name)}'.*added",
            command_output.message,
            flags=re.IGNORECASE,
        )

    # noinspection SpellCheckingInspection
    def test_apply__nominal_case(self, empty_study_860: FileStudy, command_context: CommandContext):
        recent_study = empty_study_860
        # First, prepare a new Area
        create_area = CreateArea(
            area_name="Area FR", command_context=command_context, study_version=recent_study.config.version
        )
        create_area.apply(recent_study)

        # Then, apply the command to create a new ST Storage
        pmax_injection = GEN.random((8760, 1))
        inflows = GEN.uniform(0, 1000, size=(8760, 1))
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageCreation(**PARAMETERS),
            pmax_injection=pmax_injection.tolist(),  # type: ignore
            inflows=inflows.tolist(),  # type: ignore
            study_version=recent_study.config.version,
        )
        command_output = cmd.apply(recent_study)
        assert command_output.status

        # check the config
        config = recent_study.tree.get(["input", "st-storage", "clusters", cmd.area_id, "list"])
        expected = {
            "storage1": {
                "efficiency": 0.94,
                "group": "battery",
                "initiallevel": 0.5,
                "initialleveloptim": True,
                "injectionnominalcapacity": 1500,
                "name": "Storage1",
                "reservoircapacity": 20000,
                "withdrawalnominalcapacity": 1500,
            }
        }
        assert config == expected

        # check the matrices references
        config = recent_study.tree.get(["input", "st-storage", "series", cmd.area_id])
        constants = command_context.generator_matrix_constants
        service = command_context.matrix_service
        pmax_injection_id = service.create(pd.DataFrame(pmax_injection))
        inflows_id = service.create(pd.DataFrame(inflows))
        expected = {
            "storage1": {
                "pmax_injection": f"matrix://{pmax_injection_id}",
                "pmax_withdrawal": constants.get_st_storage_pmax_withdrawal(),
                "lower_rule_curve": constants.get_st_storage_lower_rule_curve(),
                "upper_rule_curve": constants.get_st_storage_upper_rule_curve(),
                "inflows": f"matrix://{inflows_id}",
            }
        }
        assert config == expected

    # noinspection SpellCheckingInspection
    def test_to_dto(self, command_context: CommandContext):
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageCreation(**PARAMETERS),
            study_version=STUDY_VERSION_8_8,
        )

        actual = cmd.to_dto()

        expected_parameters = PARAMETERS.copy()
        # `initiallevel` = 0.5 (the default value) because `initialleveloptim` is True
        expected_parameters["initiallevel"] = 0.5
        expected_parameters["group"] = "battery"
        expected_parameters["enabled"] = True
        constants = command_context.generator_matrix_constants

        assert actual == CommandDTO(
            action=CommandName.CREATE_ST_STORAGE.value,
            version=2,
            args={
                "area_id": "area_fr",
                "parameters": expected_parameters,
                "pmax_injection": strip_matrix_protocol(constants.get_st_storage_pmax_withdrawal()),
                "pmax_withdrawal": strip_matrix_protocol(constants.get_st_storage_pmax_withdrawal()),
                "lower_rule_curve": strip_matrix_protocol(constants.get_st_storage_lower_rule_curve()),
                "upper_rule_curve": strip_matrix_protocol(constants.get_st_storage_upper_rule_curve()),
                "inflows": strip_matrix_protocol(constants.get_st_storage_inflows()),
            },
            study_version=STUDY_VERSION_8_8,
        )

    def test_get_inner_matrices(self, command_context: CommandContext):
        for study_version in (STUDY_VERSION_8_8, STUDY_VERSION_9_2):
            cmd = CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageCreation(**PARAMETERS),
                study_version=study_version,
            )
            actual = cmd.get_inner_matrices()
            constants = command_context.generator_matrix_constants
            # Ensures with the v9.2 we don't create default matrices
            if study_version == STUDY_VERSION_9_2:
                assert actual == []
            else:
                assert actual == [
                    strip_matrix_protocol(constants.get_st_storage_pmax_injection()),
                    strip_matrix_protocol(constants.get_st_storage_pmax_withdrawal()),
                    strip_matrix_protocol(constants.get_st_storage_lower_rule_curve()),
                    strip_matrix_protocol(constants.get_st_storage_upper_rule_curve()),
                    strip_matrix_protocol(constants.get_st_storage_inflows()),
                ]

    def test_version_9_2(self, command_context: CommandContext, empty_study_920: FileStudy):
        study = empty_study_920
        study_version = study.config.version
        cmd = CreateArea(area_name="Area be", command_context=command_context, study_version=study_version)
        cmd.apply(study)
        cmd = CreateArea(area_name="Area FR", command_context=command_context, study_version=study_version)
        cmd.apply(study)

        # Create a basic storage
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area fr",
            parameters=STStorageCreation(**PARAMETERS),
            study_version=study_version,
        )
        output = cmd.apply(study)
        assert output.status is True
        assert output.message == "Short-term st_storage 'Storage1' successfully added to area 'area fr'."
        # Checks ini content
        ini_path = study.config.study_path / "input" / "st-storage" / "clusters" / "area fr" / "list.ini"
        ini_content = read_ini(ini_path)
        expected_content = {
            "storage1": {
                "name": "Storage1",
                "group": "battery",
                "injectionnominalcapacity": 1500.0,
                "withdrawalnominalcapacity": 1500.0,
                "reservoircapacity": 20000.0,
                "efficiency": 0.94,
                "initiallevel": 0.5,
                "initialleveloptim": True,
                "enabled": True,
                # Ensure v9.2 fields are written with default values
                "efficiencywithdrawal": 1.0,
                "penalize-variation-injection": False,
                "penalize-variation-withdrawal": False,
            }
        }
        assert ini_content == expected_content

        # Create new st storage by specifying 9.2 properties
        parameters_9_2 = copy.deepcopy(PARAMETERS)
        parameters_9_2["group"] = "My Group"
        parameters_9_2["efficiency_withdrawal"] = 0.55
        parameters_9_2["penalize_variation_injection"] = True
        cost_injection_matrix = GEN.uniform(0, 1000, size=(8760, 1)).tolist()
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area be",
            parameters=parameters_9_2,
            cost_injection=cost_injection_matrix,
            study_version=study_version,
        )
        output = cmd.apply(study)
        assert output.status is True
        assert output.message == "Short-term st_storage 'Storage1' successfully added to area 'area be'."

        # Checks ini content
        ini_path = study.config.study_path / "input" / "st-storage" / "clusters" / "area be" / "list.ini"
        ini_content = read_ini(ini_path)
        expected_content["storage1"]["efficiencywithdrawal"] = 0.55
        expected_content["storage1"]["penalize-variation-injection"] = True
        expected_content["storage1"]["group"] = "my group"  # the group is allowed and written in lower case
        assert ini_content == expected_content

        # Checks matrices were created
        series_path = ["input", "st-storage", "series", "area be", "storage1"]
        sts_matrices = list(study.tree.get(series_path).keys())
        assert sts_matrices == [
            "pmax_injection",
            "pmax_withdrawal",
            "inflows",
            "lower_rule_curve",
            "upper_rule_curve",
            # v9.2 matrices
            "cost_injection",
            "cost_withdrawal",
            "cost_level",
            "cost_variation_injection",
            "cost_variation_withdrawal",
        ]
        # Checks more specifically the cost_injection matrix as it was given inside the command
        cost_injection = study.tree.get(series_path + ["cost_injection"])
        assert cost_injection["data"] == cost_injection_matrix
