import shutil
from pathlib import Path
from typing import Optional, Any

from antarest.core.model import JSON
from antarest.launcher.extensions.interface import ILauncherExtension
from antarest.study.storage.storage_service import StudyStorageService


class AdequacyPatchExtension(ILauncherExtension):
    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def get_name(self) -> str:
        return "adequacy_patch"

    def after_export_flat_hook(
        self,
        job_id: str,
        study_id: str,
        study_export_path: Path,
        launcher_opts: Any,
    ) -> None:
        post_processing_file = (
            Path(__file__).parent / "resources" / "post-processing.R"
        )
        shutil.copy(
            post_processing_file, study_export_path / "post-processing.R"
        )
        (
            study_config,
            study_tree,
        ) = self.storage_service.raw_study_service.study_factory.create_from_fs(
            study_export_path, study_id
        )
        study_tree.get(["user", "adequacy_patch", "config.ini"])
