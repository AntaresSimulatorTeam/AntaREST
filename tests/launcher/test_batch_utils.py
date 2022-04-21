from pathlib import Path
from typing import cast
from unittest.mock import patch, Mock, call
from zipfile import ZipFile

import pandas as pd

from antareslauncher.study_dto import StudyDTO
from antarest.core.config import Config, LauncherConfig
from antarest.launcher.adapters.slurm_launcher.batch_job import BatchJobManager
from antarest.launcher.adapters.slurm_launcher.batch_job_merge_utils import (
    merge_series_stats,
    reconstruct_synthesis,
    get_all_output_matrices,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
    Link,
    Cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
import numpy as np

from tests.conftest import with_db_context

test_dir: Path = Path(__file__).parent


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
    data_set = [
        1.005,
        1,
        2,
        3,
        5,
        6,
        2,
        2,
        8.006,
        9,
        7,
        8,
        10,
        0,
        10.0064545645,
        2,
        2,
        3,
        5,
    ]
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
    res = merge_series_stats(
        [
            (
                pd.Series([sub_set_means[i]]),
                pd.Series([subset_variances[i]]),
                len(subsets[i]),
            )
            for i in range(0, 3)
        ]
    )
    assert f"{res[0][0]:.8f}" == f"{mean:.8f}"
    assert f"{res[1][0]:.8f}" == f"{variance:.8f}"


@with_db_context
def test_prepare_batch(tmp_path: Path):
    batch_job_manager = BatchJobManager(
        "someworkspace", Mock(), Config(launcher=LauncherConfig(batch_size=4))
    )
    batch_job_manager.study_factory = Mock()

    some_study = tmp_path / "jobid"
    some_study.mkdir()
    (some_study / "somedata").touch()

    filestudy = Mock()
    batch_job_manager.study_factory.create_from_fs.return_value = filestudy

    filestudy.tree.get.side_effect = lambda x: {
        "general": {
            "nbyears": 10,
        }
    }
    assert batch_job_manager.prepare_batch_study(
        "jobid", some_study, tmp_path, force_single_batch=True
    ) == ["jobid"]

    jobs = batch_job_manager.prepare_batch_study("jobid", some_study, tmp_path)
    assert len(jobs) == 3
    assert not some_study.exists()
    assert (tmp_path / jobs[0] / "somedata").exists()
    assert (tmp_path / jobs[1] / "somedata").exists()
    assert (tmp_path / jobs[2] / "somedata").exists()
    filestudy.tree.save.assert_has_calls(
        [
            call(
                {
                    "general": {"nbyears": 10, "user-playlist": True},
                    "playlist": {
                        "playlist_reset": False,
                        "playlist_year +": [0, 1, 2, 3],
                    },
                },
                ["settings", "generaldata"],
            ),
            call(
                {
                    "general": {"nbyears": 10, "user-playlist": True},
                    "playlist": {
                        "playlist_reset": False,
                        "playlist_year +": [4, 5, 6, 7],
                    },
                },
                ["settings", "generaldata"],
            ),
            call(
                {
                    "general": {"nbyears": 10, "user-playlist": True},
                    "playlist": {
                        "playlist_reset": False,
                        "playlist_year +": [8, 9],
                    },
                },
                ["settings", "generaldata"],
            ),
        ]
    )


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
            merge_synthesis=False,
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
            merge_synthesis=False,
        )
        == target_output_dir
    )
    assert (target_output_dir / "economy" / "mc-ind" / "00001").exists()
    assert (target_output_dir / "economy" / "mc-ind" / "00002").exists()
    assert (target_output_dir / "economy" / "mc-ind" / "00003").exists()
    assert (target_output_dir / "economy" / "mc-ind" / "00004").exists()
    assert (target_output_dir / "simulation.log.1").exists()
    assert (target_output_dir / "tmp_summaries" / "mc-all.1").exists()
    assert (
        target_output_dir / "tmp_summaries" / "checkIntegrity.txt.1"
    ).exists()
    assert (
        target_output_dir / "tmp_summaries" / "annualSystemCost.txt.1"
    ).exists()
    assert (target_output_dir / "tmp_summaries" / "parameters.ini.1").exists()


def is_matrix_nearly_equal(
    test_matrix: OutputSeriesMatrix,
    ref_matrix: OutputSeriesMatrix,
    max_percent_diff: float = 0.15,
) -> bool:
    df1 = test_matrix.parse_dataframe()
    df2 = ref_matrix.parse_dataframe()
    percent_diff = ((df2 - df1) / (df1 + df2)).max().max()
    if percent_diff > max_percent_diff:
        print(test_matrix.config.path)
        print(percent_diff)
    return True


def test_merge_synthesis(tmp_path: Path):
    with ZipFile(test_dir / "assets" / "test_output.zip") as fh:
        fh.extractall(tmp_path / "to_merge" / "output")
    with ZipFile(test_dir / "assets" / "ref_output.zip") as fh:
        fh.extractall(tmp_path / "to_merge" / "output")
    study_path = tmp_path / "to_merge"
    file_study = Mock(spec=FileStudy)
    file_study.tree = Mock(spec=FileStudyTree)
    file_study.tree.context = Mock(spec=ContextServer)
    file_study.config = FileStudyTreeConfig(
        study_path=study_path,
        path=study_path,
        study_id="",
        version=-1,
        areas={
            "east": Area(
                name="east",
                links={
                    "west": Link(
                        filters_synthesis=["annual", "monthly"],
                        filters_year=["annual", "monthly"],
                    )
                },
                thermals=[
                    Cluster(id="base", name="BASE", enabled=True),
                    Cluster(id="semi base", name="SEMI BASE", enabled=True),
                    Cluster(id="peaking", name="PEAKING", enabled=True),
                ],
                renewables=[],
                filters_synthesis=["annual", "monthly"],
                filters_year=["annual", "monthly"],
            ),
            "west": Area(
                name="west",
                links={},
                thermals=[
                    Cluster(id="base", name="BASE", enabled=True),
                    Cluster(id="semi base", name="SEMI BASE", enabled=True),
                    Cluster(id="peaking", name="PEAKING", enabled=True),
                ],
                renewables=[],
                filters_synthesis=["annual", "monthly"],
                filters_year=["annual", "monthly"],
            ),
        },
        sets=None,
        outputs=Mock(),
        bindings=Mock(),
        store_new_set=False,
        archive_input_series=[],
        enr_modelling="",
    )
    reconstruct_synthesis(
        file_study, "test_output", [(0, 2), (1, 3), (2, 3), (3, 3)]
    )
    merged_matrices, _ = get_all_output_matrices(
        file_study, "test_output", [(0, 11)]
    )
    expected_matrices, _ = get_all_output_matrices(
        file_study, "ref_output", [(0, 11)]
    )
    for item_type in ["areas", "links"]:
        for item in merged_matrices[item_type]:
            for stat_element in merged_matrices[item_type][item]:
                assert is_matrix_nearly_equal(
                    merged_matrices[item_type][item][stat_element][0],
                    expected_matrices[item_type][item][stat_element][0],
                )
