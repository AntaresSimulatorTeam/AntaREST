from typing import Dict, Any, List

from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import (
    UpdateScenarioBuilder,
)

KEY_SEP = ","
HL_COEF = 100


class ScenarioBuilderManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_config(self, study: Study) -> Dict[str, Any]:
        temp = self.storage_service.get_storage(study).get(
            study, "/settings/scenariobuilder"
        )

        def format_key(key: str) -> List[str]:
            parts = key.split(KEY_SEP)
            # "ntc,area1,area2,0" to ["ntc", "area1 / area2", "0"]
            if parts[0] == "ntc":
                return [parts[0], f"{parts[1]} / {parts[2]}", parts[3]]
            # "t,area1,0,thermal1" to ["t", "area1", "thermal1", "0"]
            elif parts[0] == "t":
                return [parts[0], parts[1], parts[3], parts[2]]
            # "[symbol],area1,0" to [[symbol], "area1", "0"]
            return parts

        def format_obj(obj: Dict[str, Any]) -> Dict[str, Any]:
            result = {}
            for k, v in obj.items():
                if isinstance(v, dict):
                    result[k] = format_obj(v)
                else:
                    keys = format_key(k)
                    nested_dict = result
                    for key in keys[:-1]:
                        nested_dict = nested_dict.setdefault(key, {})
                    nested_dict[keys[-1]] = (
                        v * HL_COEF if keys[0] == "hl" else v
                    )
            return result

        return format_obj(temp)

    def update_config(self, study: Study, data: Dict[str, Any]) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        def to_valid_key(key: str) -> str:
            parts = key.split(KEY_SEP)
            # "ntc,area1 / area2,0" to "ntc,area1,area2,0"
            if parts[0] == "ntc":
                area1, area2 = parts[1].split(" / ")
                return KEY_SEP.join([parts[0], area1, area2, parts[2]])
            # "t,area1,thermal1,0" to "t,area1,0,thermal1"
            elif parts[0] == "t":
                return KEY_SEP.join([parts[0], parts[1], parts[3], parts[2]])
            # "[symbol],area1,0"
            return key

        def flatten_obj(
            obj: Dict[str, Any], parent_key: str = ""
        ) -> Dict[str, Dict[str, int]]:
            items = []  # type: ignore
            for k, v in obj.items():
                new_key = parent_key + KEY_SEP + k if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_obj(v, new_key).items())
                else:
                    symbol = new_key.split(KEY_SEP)[0]
                    items.append(
                        (
                            to_valid_key(new_key),
                            v / HL_COEF if symbol == "hl" else v,
                        )
                    )
            return dict(items)

        execute_or_add_commands(
            study,
            file_study,
            [
                UpdateScenarioBuilder(
                    # The value is a string when it is a ruleset cloning/deleting
                    data={
                        k: flatten_obj(v) if isinstance(v, dict) else v
                        for k, v in data.items()
                    },
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            ],
            self.storage_service,
        )
