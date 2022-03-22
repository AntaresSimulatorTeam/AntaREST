import json
import logging
import shutil
from pathlib import Path
from typing import Optional, Any, cast, List, Dict

import yaml
from filelock import FileLock

from antarest.core.config import Config
from antarest.core.configdata.model import ConfigData
from antarest.core.configdata.repository import ConfigDataRepository
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import JSON
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import assert_this
from antarest.launcher.extensions.interface import ILauncherExtension
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService

logger = logging.getLogger(__name__)


class AdequacyPatchExtension(ILauncherExtension):
    EXTENSION_NAME = "adequacy_patch"

    def __init__(self, study_service: StudyService, config: Config):
        self.study_service = study_service
        self.tmp_dir = (
            config.storage.tmp_dir
            / f"ext_{AdequacyPatchExtension.EXTENSION_NAME}"
        )
        self.config_data_repo = ConfigDataRepository()
        self.tmp_dir.mkdir(exist_ok=True)

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

    def _check_config(self, study_id: str, study_export_path: Path) -> JSON:
        (
            study_config,
            study_tree,
        ) = self.study_service.storage_service.raw_study_service.study_factory.create_from_fs(
            study_export_path, study_id, use_cache=False
        )
        user_config = study_tree.get(["user"])
        assert_this("flowbased" in user_config or "Flowbased" in user_config)
        adequacy_patch_config = yaml.safe_load(
            cast(
                bytes, study_tree.get(["user", "adequacypatch", "config.yml"])
            )
        )
        assert_this("areas" in adequacy_patch_config)
        return cast(JSON, adequacy_patch_config)

    def prepare_study_for_adq_patch(
        self, job_id: str, study: FileStudy, adq_patch_config: JSON
    ) -> Dict[str, bool]:
        area_to_turn_on: List[str] = [
            transform_name_to_id(area_id)
            for area_id in adq_patch_config.get("areas", [])
        ]
        original_area_status: Dict[str, bool] = {}
        for area_id, area in study.config.areas.items():
            # area.filters_synthesis
            original_area_status[area_id] = "hourly" in area.filters_year
            if (
                not original_area_status[area_id]
                and area_id in area_to_turn_on
            ):
                study.tree.save(
                    True,
                    [
                        "input",
                        "areas",
                        area_id,
                        "optimization",
                        "filter-year-by-year",
                    ],
                )

        with FileLock(self.tmp_dir / "data.lock"):
            with db():
                key = "ADEQUACY_PATCH_DATA"
                data = json.loads(self.config_data_repo.get(key, 0) or "{}")
                data[job_id] = original_area_status
                self.config_data_repo.save(
                    ConfigData(owner=0, key=key, value=json.dumps(data))
                )
        return original_area_status

    def before_import_hook(
        self,
        job_id: str,
        study_id: str,
        study_output_path: Path,
        ext_opts: Any,
    ) -> None:
        with FileLock(self.tmp_dir / "data.lock"):
            with db():
                key = "ADEQUACY_PATCH_DATA"
                data = json.loads(self.config_data_repo.get(key, 0) or "{}")
                original_area_status = data.get(job_id, {})
                if job_id in data:
                    del data[job_id]
                    self.config_data_repo.save(
                        ConfigData(owner=0, key=key, value=json.dumps(data))
                    )

        study_metadata = self.study_service.get_study(study_id)
        study = self.study_service.storage_service.get_storage(
            study_metadata
        ).get_raw(
            study_metadata, use_cache=False, output_dir=study_output_path
        )
        for area_id, keep in original_area_status.items():
            if not keep:
                # delete the values-hourly for that area..
                # study_tree.delete(["output", output_path, outputs[0].mode, "mc-ind", "*", ])
                pass
