import logging
import shutil
from pathlib import Path
from typing import Optional, Any, cast

import yaml

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.launcher.extensions.interface import ILauncherExtension
from antarest.study.storage.storage_service import StudyStorageService

logger = logging.getLogger(__name__)


class AdequacyPatchExtension(ILauncherExtension):
    EXTENSION_NAME = "adequacy_patch"

    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def get_name(self) -> str:
        return AdequacyPatchExtension.EXTENSION_NAME

    def after_export_flat_hook(
        self,
        job_id: str,
        study_id: str,
        study_export_path: Path,
        launcher_opts: Any,
    ) -> None:
        logger.info("Applying adequacy patch postprocessing script")
        post_processing_file = (
            Path(__file__).parent / "resources" / "post-processing.R"
        )
        shutil.copy(
            post_processing_file, study_export_path / "post-processing.R"
        )
        self._check_config(study_id, study_export_path)

    def _check_config(self, study_id: str, study_export_path: Path) -> None:
        (
            study_config,
            study_tree,
        ) = self.storage_service.raw_study_service.study_factory.create_from_fs(
            study_export_path, study_id
        )
        user_config = study_tree.get(["user"])
        assert_this("flowbased" in user_config or "Flowbased" in user_config)
        adequacy_patch_config = yaml.safe_load(
            cast(
                bytes, study_tree.get(["user", "adequacypatch", "config.yml"])
            )
        )
        assert_this("areas" in adequacy_patch_config)
