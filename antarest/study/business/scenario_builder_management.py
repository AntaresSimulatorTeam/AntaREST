from typing import Dict, Any, List

from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)


class ScenarioBuilderManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_config(self, study: Study) -> Dict[str, Any]:
        temp = self.storage_service.get_storage(study).get(
            study, "/settings/scenariobuilder"
        )

        def format_key(key: str) -> List[str]:
            parts = key.split(",")
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
                    nested_dict[keys[-1]] = v * 100 if keys[0] == "hl" else v
            return result

        return format_obj(temp)

    def set_config(self, study: Study, config: Dict[str, Any]) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        execute_or_add_commands(
            study,
            file_study,
            [
                UpdateConfig(
                    target="settings/scenariobuilder",
                    data=config,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            ],
            self.storage_service,
        )
