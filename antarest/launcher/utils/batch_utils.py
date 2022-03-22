import shutil
import uuid
from pathlib import Path
from typing import List

from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers


BATCH_SIZE = 100


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
    batch_params = compute_batch_params(study)
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
    job_ids: List[str], outputs_dir: Path, output_target_dir: Path
) -> None:
    pass
