import pytest
from antares.study.version import StudyVersion

from antarest.study.business.model.config.general_model import BuildingMode, GeneralConfig
from antarest.study.business.model.scenario_builder_model import DEFAULT_RULESET_NAME
from antarest.study.storage.rawstudy.model.filesystem.config.general import GeneralFileData


class TestToModel:
    @pytest.mark.parametrize(
        "ini_flags, expected_mode",
        [
            ({"derated": True}, BuildingMode.DERATED),
            ({"custom_scenario": True}, BuildingMode.CUSTOM),
            ({"custom_ts_numbers": True}, BuildingMode.CUSTOM),
            ({}, BuildingMode.AUTOMATIC),
        ],
    )
    def test_building_mode_mapping(self, ini_flags: dict, expected_mode: BuildingMode) -> None:
        file_data = GeneralFileData.model_validate(ini_flags)
        assert file_data.to_model().building_mode == expected_mode


class TestFromModel:
    @pytest.mark.parametrize(
        "building_mode, version, expected",
        [
            (
                BuildingMode.DERATED,
                "8.6",
                {"derated": True, "custom_scenario": None, "active_rules_scenario": None},
            ),
            (
                BuildingMode.AUTOMATIC,
                "8.6",
                {"derated": False, "custom_scenario": False, "active_rules_scenario": None},
            ),
            (
                BuildingMode.CUSTOM,
                "8.6",
                {
                    "derated": False,
                    "custom_scenario": True,
                    "custom_ts_numbers": None,
                    "active_rules_scenario": DEFAULT_RULESET_NAME.lower(),
                },
            ),
            (
                BuildingMode.CUSTOM,
                "7.2",
                {
                    "derated": False,
                    "custom_scenario": None,
                    "custom_ts_numbers": True,
                    "active_rules_scenario": DEFAULT_RULESET_NAME.lower(),
                },
            ),
        ],
    )
    def test_building_mode_serialization(self, building_mode: BuildingMode, version: str, expected: dict) -> None:
        config = GeneralConfig(building_mode=building_mode)
        file_data = GeneralFileData.from_model(config, StudyVersion.parse(version))
        for field, value in expected.items():
            assert getattr(file_data, field) == value, f"{field}: expected {value}, got {getattr(file_data, field)}"
