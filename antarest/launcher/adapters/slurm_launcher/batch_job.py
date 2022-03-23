import logging
import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional, List

from filelock import FileLock

from antareslauncher.study_dto import StudyDTO
from antarest.core.config import Config
from antarest.core.configdata.model import ConfigData
from antarest.core.configdata.repository import ConfigDataRepository
from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.utils import find_single_output_path


logger = logging.getLogger(__name__)

BATCH_JOB_CONFIG_DATA_KEY = "BATCH_JOBS"
BATCH_SIZE = 100


class BatchJobManager:
    def __init__(self, workspace_id: str, config: Config):
        self.config_data_repo = ConfigDataRepository()
        self.lock_file = config.storage.tmp_dir / "batchjobmanager.lock"
        self.workspace_id = workspace_id
        self.cache: Dict[str, str] = {}
        self._init()

    def _init(self) -> None:
        self.cache = self.get_batch_jobs()

    def get_batch_jobs(self) -> Dict[str, str]:
        all_jobs = (
            self.config_data_repo.get_json(key=BATCH_JOB_CONFIG_DATA_KEY) or {}
        )
        return all_jobs.get(self.workspace_id, {})

    def add_batch_job(
        self, parent_job_id: str, batch_job_ids: List[str]
    ) -> None:
        with FileLock(self.lock_file):
            all_jobs = (
                self.config_data_repo.get_json(key=BATCH_JOB_CONFIG_DATA_KEY)
                or {}
            )
            workspace_jobs = all_jobs.get(self.workspace_id, {})
            for batch_job_id in batch_job_ids:
                workspace_jobs[batch_job_id] = parent_job_id
            all_jobs[self.workspace_id] = workspace_jobs
            self.config_data_repo.put_json(
                key=BATCH_JOB_CONFIG_DATA_KEY, data=all_jobs
            )

    def remove_batch_job(self, parent_job_id: str) -> None:
        with FileLock(self.lock_file):
            all_jobs = (
                self.config_data_repo.get_json(key=BATCH_JOB_CONFIG_DATA_KEY)
                or {}
            )
            workspace_jobs = all_jobs.get(self.workspace_id, {})
            workspace_jobs = {
                job_id: parent_id
                for job_id, parent_id in workspace_jobs.items()
                if parent_id != parent_job_id
            }
            all_jobs[self.workspace_id] = workspace_jobs
            self.config_data_repo.put_json(
                key=BATCH_JOB_CONFIG_DATA_KEY, data=all_jobs
            )

    def get_batch_job_parent(self, batch_job_id: str) -> Optional[str]:
        return self.cache.get(batch_job_id, None)

    def get_batch_job_children(self, parent_batch_job_id: str) -> List[str]:
        return [
            child
            for child, parent in self.cache.items()
            if parent_batch_job_id == parent
        ]

    @staticmethod
    def compute_batch_params(study: FileStudy) -> List[List[int]]:
        playlist = FileStudyHelpers.get_playlist(study)
        playlist_len = len(playlist)
        if playlist_len > 100:
            batchs = []
            i = 0
            while True:
                upper_bound = BATCH_SIZE * (1 + i)
                if upper_bound >= playlist_len:
                    batchs.append(playlist[BATCH_SIZE * i : playlist_len])
                    break
                batchs.append(playlist[BATCH_SIZE * i : upper_bound])
                i += 1
            return batchs
        return [playlist]

    @staticmethod
    def prepare_batch_study(
        job_id: str,
        raw_study_path: Path,
        study_factory: StudyFactory,
        workspace: Path,
    ) -> List[str]:
        study_config, study_tree = study_factory.create_from_fs(
            raw_study_path, study_id=job_id
        )
        study = FileStudy(study_config, study_tree)
        batch_params = BatchJobManager.compute_batch_params(study)
        assert_this(len(batch_params) > 0)
        FileStudyHelpers.set_playlist(study, batch_params[0])

        sub_jobs = []
        for playlist in batch_params[1:]:
            sub_job_id = str(uuid.uuid4())
            shutil.copytree(raw_study_path, workspace / sub_job_id)
            study_config, study_tree = study_factory.create_from_fs(
                workspace / sub_job_id, study_id=job_id
            )
            study = FileStudy(study_config, study_tree)
            FileStudyHelpers.set_playlist(study, playlist)
            sub_jobs.append(sub_job_id)

        sub_job_id = str(uuid.uuid4())
        shutil.move(str(raw_study_path), str(workspace / sub_job_id))
        sub_jobs.append(sub_job_id)
        return sub_jobs

    def merge_outputs(
        self,
        job_id: str,
        launcher_studies: List[StudyDTO],
        workspace: Path,
        allow_part_failure: bool = True,
    ) -> Optional[Path]:
        assert_this(len(launcher_studies) > 0)
        output_dir: Optional[Path] = None
        batch_parts = 0
        for study in launcher_studies:
            if not study.with_error:
                batch_parts += 1
                batch_output_dir = find_single_output_path(
                    workspace / study.name / "output"
                )
                if not output_dir:
                    output_dir = batch_output_dir
                else:
                    BatchJobManager.merge_output_data(
                        batch_output_dir, output_dir
                    )
            elif not allow_part_failure:
                logger.warning(
                    f"Sub job {study.name} failed within job {job_id}. Importing nothing."
                )
                return None
            else:
                logger.warning(
                    f"Sub job {study.name} failed within job {job_id}. Skipping importing this part."
                )
        if batch_parts > 1 and output_dir:
            BatchJobManager.reconstruct_synthesis(output_dir)
        return output_dir

    @staticmethod
    def merge_output_data(batch_output_dir: Path, output_dir: Path) -> None:
        pass

    @staticmethod
    def reconstruct_synthesis(output_dir: Path) -> None:
        pass
