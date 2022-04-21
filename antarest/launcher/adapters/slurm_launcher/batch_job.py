import logging
import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional, List, Tuple

from filelock import FileLock
from pandas import Series, MultiIndex, DataFrame  # type: ignore

from antareslauncher.study_dto import StudyDTO
from antarest.core.config import Config
from antarest.core.configdata.repository import ConfigDataRepository
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import assert_this
from antarest.launcher.adapters.slurm_launcher.batch_job_merge_utils import (
    reconstruct_synthesis,
    merge_output_data,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.utils import find_single_output_path


logger = logging.getLogger(__name__)

BATCH_JOB_CONFIG_DATA_KEY = "BATCH_JOBS"


class BatchJobManager:
    def __init__(
        self, workspace_id: str, study_factory: StudyFactory, config: Config
    ):
        self.batch_size = config.launcher.batch_size
        self.config_data_repo = ConfigDataRepository()
        self.study_factory = study_factory
        self.lock_file = config.storage.tmp_dir / "batchjobmanager.lock"
        self.workspace_id = workspace_id
        self.cache: Dict[str, str] = {}

    def refresh_cache(self) -> None:
        self.cache = self._get_batch_jobs()

    def _get_batch_jobs(self, all_workspaces: bool = False) -> Dict[str, str]:
        with db():
            all_jobs = (
                self.config_data_repo.get_json(key=BATCH_JOB_CONFIG_DATA_KEY)
                or {}
            )
            if all_workspaces:
                all_workspaces_jobs: Dict[str, str] = {}
                for workspace_jobs in all_jobs.values():
                    all_workspaces_jobs = {
                        **workspace_jobs,
                        **all_workspaces_jobs,
                    }
                return all_workspaces_jobs
            return all_jobs.get(self.workspace_id, {})

    def _add_batch_job(
        self, parent_job_id: str, batch_job_ids: List[str]
    ) -> None:
        with FileLock(self.lock_file):
            with db():
                all_jobs = (
                    self.config_data_repo.get_json(
                        key=BATCH_JOB_CONFIG_DATA_KEY
                    )
                    or {}
                )
                workspace_jobs = all_jobs.get(self.workspace_id, {})
                for batch_job_id in batch_job_ids:
                    workspace_jobs[batch_job_id] = parent_job_id
                all_jobs[self.workspace_id] = workspace_jobs
                self.config_data_repo.put_json(
                    key=BATCH_JOB_CONFIG_DATA_KEY, data=all_jobs
                )
                self.cache = workspace_jobs

    def remove_batch_job(self, parent_job_id: str) -> None:
        with FileLock(self.lock_file):
            with db():
                all_jobs = (
                    self.config_data_repo.get_json(
                        key=BATCH_JOB_CONFIG_DATA_KEY
                    )
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
                self.cache = workspace_jobs

    def get_batch_job_parent(self, batch_job_id: str) -> Optional[str]:
        return self.cache.get(batch_job_id, None)

    def get_batch_job_children(
        self,
        parent_batch_job_id: str,
        use_cache: bool = True,
        from_all_workspaces: bool = False,
    ) -> List[str]:
        if not use_cache:
            self.refresh_cache()
        jobs = (
            self.cache.items()
            if not from_all_workspaces
            else self._get_batch_jobs(all_workspaces=True).items()
        )
        return [
            child for child, parent in jobs if parent_batch_job_id == parent
        ]

    @staticmethod
    def compute_batch_params(
        study: FileStudy, batch_size: int
    ) -> List[List[int]]:
        """
        Compute list of playlist years which count do not exceed a configured batch size.
        """
        playlist = FileStudyHelpers.get_playlist(study)
        playlist_len = len(playlist)
        if playlist_len > batch_size:
            batchs = []
            i = 0
            while True:
                upper_bound = batch_size * (1 + i)
                if upper_bound >= playlist_len:
                    batchs.append(playlist[batch_size * i : playlist_len])
                    break
                batchs.append(playlist[batch_size * i : upper_bound])
                i += 1
            return batchs
        return [playlist]

    def prepare_batch_study(
        self,
        job_id: str,
        raw_study_path: Path,
        workspace: Path,
        force_single_batch: bool = False,
    ) -> List[str]:
        """
        Split a study into multiple batches using playlist to control which year to run.
        The study is copied into a new directory named after the sub job id and generaldata playlist is updated.
        The the array of sub job is registered with reference to the original job_id as parent.

        If the configured playlist / number of year to run is less than a batch configured size or forced to use a single batch
        nothing is done and the sub job id is the same as the parent id
        """
        study = self.study_factory.create_from_fs(
            raw_study_path, study_id=job_id
        )
        batch_params = (
            BatchJobManager.compute_batch_params(study, self.batch_size)
            if not force_single_batch
            else []
        )

        if len(batch_params) <= 1:
            self._add_batch_job(job_id, [job_id])
            return [job_id]

        FileStudyHelpers.set_playlist(study, batch_params[0])
        sub_jobs = []
        for playlist in batch_params[1:]:
            sub_job_id = str(uuid.uuid4())
            shutil.copytree(raw_study_path, workspace / sub_job_id)
            study = self.study_factory.create_from_fs(
                workspace / sub_job_id, study_id=job_id
            )
            FileStudyHelpers.set_playlist(study, playlist)
            sub_jobs.append(sub_job_id)

        sub_job_id = str(uuid.uuid4())
        shutil.move(str(raw_study_path), str(workspace / sub_job_id))
        sub_jobs.append(sub_job_id)
        self._add_batch_job(job_id, sub_jobs)
        return sub_jobs

    def merge_outputs(
        self,
        job_id: str,
        launcher_studies: List[StudyDTO],
        workspace: Path,
        allow_part_failure: bool = True,
        merge_synthesis: bool = True,
    ) -> Optional[Path]:
        """
        Merge the output of study run batches.
        The first output directory found (study done with no error) is taken as the main output where everything will be merged.
        This way, in the case of a single batch, nothing is done.
        Merging is done in two steps:
        - copying each output data in the correct place (mc-ind) or temporary places (mc-all, synthesis files, parameters)
        - merging the synthesis
        """
        assert_this(len(launcher_studies) > 0)
        output_dir: Optional[Path] = None
        output_info: Optional[Tuple[Path, str]] = None
        batch_parts = 0
        merged_batches: List[Tuple[int, int]] = []
        for study in launcher_studies:
            if not study.with_error:
                batch_output_dir = find_single_output_path(
                    workspace / study.name / "output"
                )
                if not output_dir:
                    output_dir = batch_output_dir
                    output_info = (
                        workspace / study.name,
                        batch_output_dir.name,
                    )
                batch_size = merge_output_data(
                    batch_output_dir, output_dir, batch_parts
                )
                merged_batches.append((batch_parts, batch_size))
                batch_parts += 1
            elif not allow_part_failure:
                logger.warning(
                    f"Sub job {study.name} failed within job {job_id}. Importing nothing."
                )
                return None
            else:
                logger.warning(
                    f"Sub job {study.name} failed within job {job_id}. Skipping importing this part."
                )
        if batch_parts > 1 and output_info and merge_synthesis:
            file_study = self.study_factory.create_from_fs(
                output_info[0], "", use_cache=False
            )
            reconstruct_synthesis(file_study, output_info[1], merged_batches)
        # TODO remove tmp copied files (mc.all, summary files, etc.)
        return output_dir
