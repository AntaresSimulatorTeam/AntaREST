from typing import Optional

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyHelpers:
    @staticmethod
    def get_config(study: FileStudy, output_id: Optional[str]) -> JSON:
        config_path = ["settings", "generaldata"]
        if output_id:
            config_path = [
                "output",
                output_id,
                "about-the-study",
                "parameters",
            ]
        return study.tree.get(config_path)
