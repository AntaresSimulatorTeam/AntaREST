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
import pytest
from pydantic import ValidationError

from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorage880Properties,
    STStorageGroup,
    STStorageProperties,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.study_upgrader import StudyUpgrader
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import REQUIRED_VERSION, CreateSTStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.model import CommandDTO

GEN = np.random.default_rng(1000)


@pytest.fixture(name="recent_study")
def recent_study_fixture(empty_study: FileStudy) -> FileStudy:
    """
    Fixture for creating a recent version of the FileStudy object.

    Args:
        empty_study: The empty FileStudy object used as model.

    Returns:
        FileStudy: The FileStudy object upgraded to the required version.
    """
    StudyUpgrader(empty_study.config.study_path, str(REQUIRED_VERSION)).upgrade()
    empty_study.config.version = REQUIRED_VERSION
    return empty_study


# The parameter names to be used are those in the INI file.
# Non-string values are automatically converted into strings.
# noinspection SpellCheckingInspection
PARAMETERS = {
    "name": "Storage1",
    "group": "Battery",
    "injectionnominalcapacity": 1500,
    "withdrawalnominalcapacity": 1500,
    "reservoircapacity": 20000,
    "efficiency": 0.94,
    "initialleveloptim": True,
}

# noinspection SpellCheckingInspection
OTHER_PARAMETERS = {
    "name": "Storage1",
    "group": "Battery",
    "injectionnominalcapacity": 1200,
    "withdrawalnominalcapacity": 1300,
    "reservoircapacity": 20500,
    "efficiency": 0.92,
    "initiallevel": 0,
    "initialleveloptim": True,
}


class TestCreateSTStorage:
    # noinspection SpellCheckingInspection
    def test_init(self, command_context: CommandContext):
        pmax_injection = GEN.random((8760, 1))
        inflows = GEN.uniform(0, 1000, size=(8760, 1))
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageProperties(**PARAMETERS),
            pmax_injection=pmax_injection.tolist(),  # type: ignore
            inflows=inflows.tolist(),  # type: ignore
            study_version=STUDY_VERSION_8_8,
        )

        # Check the attribues
        assert cmd.command_name == CommandName.CREATE_ST_STORAGE
        assert cmd.study_version == STUDY_VERSION_8_8
        assert cmd.command_context == command_context
        assert cmd.area_id == "area_fr"
        expected_parameters = {k: str(v) for k, v in PARAMETERS.items()}
        assert cmd.parameters == STStorageProperties(**expected_parameters)

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
            parameters=STStorage880Properties(**PARAMETERS),
            study_version=STUDY_VERSION_8_8,
        )
        assert cmd.parameters.group == STStorageGroup.BATTERY

    def test_init__invalid_storage_name(self, recent_study: FileStudy, command_context: CommandContext):
        # When we apply the config for a new ST Storage with a bad name
        with pytest.raises(ValidationError) as ctx:
            parameters = {**PARAMETERS, "name": "?%$$"}  # bad name
            CreateSTStorage(
                command_context=command_context,
                area_id="dummy",
                parameters=STStorageProperties(**parameters),
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
                parameters=STStorageProperties(**PARAMETERS),
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
                parameters=STStorageProperties(**PARAMETERS),
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
                parameters=STStorageProperties(**PARAMETERS),
                pmax_injection=array.tolist(),  # type: ignore
                study_version=STUDY_VERSION_8_8,
            )
        assert ctx.value.error_count() == 1
        raised_error = ctx.value.errors()[0]
        assert raised_error["type"] == "value_error"
        assert raised_error["msg"] == "Value error, Matrix values cannot contain NaN"
        assert "pmax_injection" in raised_error["input"]

    def test_init__invalid_matrix_type(self, command_context: CommandContext):
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageProperties(**PARAMETERS),
                pmax_injection=[1, 2, 3],
                study_version=STUDY_VERSION_8_8,
            )
        assert ctx.value.error_count() == 1
        raised_error = ctx.value.errors()[0]
        assert raised_error["type"] == "value_error"
        assert raised_error["msg"] == "Value error, Invalid matrix shape (3,), expected (8760, 1)"
        assert "pmax_injection" in raised_error["input"]

    def test_apply_config__invalid_version(self, empty_study: FileStudy, command_context: CommandContext):
        # Given an old study in version 720
        # When we apply the config to add a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id="foo",
            parameters=STStorageProperties(**PARAMETERS),
            study_version=empty_study.config.version,
        )
        command_output = create_st_storage.apply_config(empty_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"Invalid.*version {empty_study.config.version}",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_config__missing_area(self, recent_study: FileStudy, command_context: CommandContext):
        # Given a study without "unknown area" area
        # When we apply the config to add a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id="unknown area",  # bad ID
            parameters=STStorageProperties(**PARAMETERS),
            study_version=recent_study.config.version,
        )
        command_output = create_st_storage.apply_config(recent_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"'{re.escape(create_st_storage.area_id)}'.*does not exist",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_config__duplicate_storage(self, recent_study: FileStudy, command_context: CommandContext):
        # First, prepare a new Area
        create_area = CreateArea(
            area_name="Area FR", command_context=command_context, study_version=recent_study.config.version
        )
        create_area.apply(recent_study)

        # Then, apply the config for a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageProperties(**PARAMETERS),
            study_version=recent_study.config.version,
        )
        command_output = create_st_storage.apply_config(recent_study.config)
        assert command_output.status is True

        # Then, apply the config a second time
        parameters = {**PARAMETERS, "name": "STORAGE1"}  # different case
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageProperties(**parameters),
            study_version=recent_study.config.version,
        )
        command_output = create_st_storage.apply_config(recent_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"'{re.escape(create_st_storage.storage_name)}'.*already exists",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_config__nominal_case(self, recent_study: FileStudy, command_context: CommandContext):
        # First, prepare a new Area
        create_area = CreateArea(
            area_name="Area FR", command_context=command_context, study_version=recent_study.config.version
        )
        create_area.apply(recent_study)

        # Then, apply the config for a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageProperties(**PARAMETERS),
            study_version=recent_study.config.version,
        )
        command_output = create_st_storage.apply_config(recent_study.config)

        # Check the command output and extra dict
        assert command_output.status is True
        assert re.search(
            rf"'{re.escape(create_st_storage.storage_name)}'.*added",
            command_output.message,
            flags=re.IGNORECASE,
        )

    # noinspection SpellCheckingInspection
    def test_apply__nominal_case(self, recent_study: FileStudy, command_context: CommandContext):
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
            parameters=STStorageProperties(**PARAMETERS),
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
        pmax_injection_id = service.create(pmax_injection)
        inflows_id = service.create(inflows)
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

    def test_apply__invalid_apply_config(self, empty_study: FileStudy, command_context: CommandContext):
        # First, prepare a new Area
        create_area = CreateArea(
            area_name="Area FR", command_context=command_context, study_version=empty_study.config.version
        )
        create_area.apply(empty_study)

        # Then, apply the command to create a new ST Storage
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageProperties(**PARAMETERS),
            study_version=empty_study.config.version,
        )
        command_output = cmd.apply(empty_study)
        assert not command_output.status  # invalid study (too old)

    # noinspection SpellCheckingInspection
    def test_to_dto(self, command_context: CommandContext):
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageProperties(**PARAMETERS),
            study_version=STUDY_VERSION_8_8,
        )

        actual = cmd.to_dto()

        expected_parameters = PARAMETERS.copy()
        # `initiallevel` = 0.5 (the default value) because `initialleveloptim` is True
        expected_parameters["initiallevel"] = 0.5
        expected_parameters["group"] = "battery"
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
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageProperties(**PARAMETERS),
            study_version=STUDY_VERSION_8_8,
        )
        actual = cmd.get_inner_matrices()
        constants = command_context.generator_matrix_constants
        assert actual == [
            strip_matrix_protocol(constants.get_st_storage_pmax_injection()),
            strip_matrix_protocol(constants.get_st_storage_pmax_withdrawal()),
            strip_matrix_protocol(constants.get_st_storage_lower_rule_curve()),
            strip_matrix_protocol(constants.get_st_storage_upper_rule_curve()),
            strip_matrix_protocol(constants.get_st_storage_inflows()),
        ]
