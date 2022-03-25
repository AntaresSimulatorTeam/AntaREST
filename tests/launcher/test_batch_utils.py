from pathlib import Path
from typing import cast
from unittest.mock import patch, Mock

from antareslauncher.study_dto import StudyDTO
from antarest.core.config import Config, LauncherConfig
from antarest.launcher.adapters.slurm_launcher.batch_job import BatchJobManager
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
import numpy as np


@patch.object(FileStudyHelpers, "get_playlist")
def test_batch_compute_params(get_playlist_mock):
    playlist = [year for year in range(0, 102)]
    get_playlist_mock.return_value = playlist
    batch = BatchJobManager.compute_batch_params(Mock(), 100)
    assert len(batch) == 2
    assert batch[1] == [100, 101]

    playlist = [year for year in range(0, 100)]
    get_playlist_mock.return_value = playlist
    batch = BatchJobManager.compute_batch_params(Mock(), 100)
    assert len(batch) == 1

    playlist = [year for year in range(0, 200)]
    get_playlist_mock.return_value = playlist
    batch = BatchJobManager.compute_batch_params(Mock(), 100)
    assert len(batch) == 2
    assert len(batch[1]) == 100


def test_merge_stats():
    data_set = [1, 1, 2, 3, 5, 6, 2, 2, 8, 9, 7, 8, 10, 0, 10, 2, 2, 3, 5]
    subset_1 = data_set[0:5]
    subset_2 = data_set[5:12]
    subset_3 = data_set[12:]
    subsets = [subset_1, subset_2, subset_3]
    assert data_set == subset_1 + subset_2 + subset_3
    mean = np.mean(data_set)
    sub_set_means = [cast(float, np.mean(subset)) for subset in subsets]
    variance = np.sqrt(np.var(data_set))
    subset_variances = [
        cast(float, np.sqrt(np.var(subset))) for subset in subsets
    ]
    res = BatchJobManager.merge_stats(
        [
            (sub_set_means[i], subset_variances[i], len(subsets[i]))
            for i in range(0, 3)
        ]
    )
    assert f"{res[0]:.8f}" == f"{mean:.8f}"
    assert f"{res[1]:.8f}" == f"{variance:.8f}"


def test_merge_outputs(tmp_path: Path):
    batch_job_manager = BatchJobManager(
        "someworkspace", Mock(), Config(launcher=LauncherConfig(batch_size=10))
    )
    batch0_study = tmp_path / "final"
    target_output_dir = tmp_path / "final" / "output"
    batch1_study = tmp_path / "batch1"
    batch2_study = tmp_path / "batch2"
    batch1_output = batch1_study / "output"
    batch2_output = batch2_study / "output"

    target_output_dir.mkdir(parents=True)
    batch2_output.mkdir(parents=True)

    assert (
        batch_job_manager.merge_outputs(
            "job_id",
            [
                StudyDTO(path=str(batch0_study), with_error=True),
                StudyDTO(path=str(batch1_study), with_error=False),
            ],
            workspace=tmp_path,
            allow_part_failure=False,
        )
        is None
    )

    (target_output_dir / "economy" / "mc-ind").mkdir(parents=True)
    (target_output_dir / "simulation.log").touch()
    (batch1_output / "economy" / "mc-ind").mkdir(parents=True)
    (batch1_output / "economy" / "mc-ind" / "00001").mkdir()
    (batch1_output / "economy" / "mc-ind" / "00002").mkdir()
    (batch1_output / "economy" / "mc-ind" / "00003").mkdir()
    (batch1_output / "economy" / "mc-ind" / "00004").mkdir()
    (batch1_output / "simulation.log").touch()
    (batch1_output / "economy" / "mc-all").mkdir()
    (batch1_output / "checkIntegrity.txt").touch()
    (batch1_output / "annualSystemCost.txt").touch()
    (batch1_output / "about-the-study").mkdir()
    (batch1_output / "about-the-study" / "parameters.ini").touch()

    assert (
        batch_job_manager.merge_outputs(
            "job_id",
            [
                StudyDTO(path=str("failed"), with_error=True),
                StudyDTO(path=str(batch0_study), with_error=False),
                StudyDTO(path=str(batch1_study), with_error=False),
            ],
            workspace=tmp_path,
            allow_part_failure=True,
        )
        == target_output_dir
    )
    assert (target_output_dir / "economy" / "mc-ind" / "00001").exists()
    assert (target_output_dir / "economy" / "mc-ind" / "00002").exists()
    assert (target_output_dir / "economy" / "mc-ind" / "00003").exists()
    assert (target_output_dir / "economy" / "mc-ind" / "00004").exists()
    assert (target_output_dir / "simulation.log.2").exists()
    assert (target_output_dir / "tmp_summaries" / "mc-all.2").exists()
    assert (
        target_output_dir / "tmp_summaries" / "checkIntegrity.txt.2"
    ).exists()
    assert (
        target_output_dir / "tmp_summaries" / "annualSystemCost.txt.2"
    ).exists()
    assert (target_output_dir / "tmp_summaries" / "parameters.ini.2").exists()
