from typing import Dict, Any

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

        def transform(obj: Dict[str, Any]) -> Dict[str, Any]:
            result = {}
            for k, v in obj.items():
                if isinstance(v, dict):
                    result[k] = transform(v)
                else:
                    keys = k.split(",")
                    nested_dict = result
                    for key in keys[:-1]:
                        nested_dict = nested_dict.setdefault(key, {})
                    nested_dict[keys[-1]] = v
            return result

        return transform(temp)

    def set_config(self, study: Study, config: Dict[str, Any]) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        execute_or_add_commands(
            study,
            file_study,
            [
                UpdateConfig(
                    target="/settings/scenariobuilder",
                    data=config,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            ],
            self.storage_service,
        )
