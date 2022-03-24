from pathlib import Path
from unittest.mock import patch, Mock

from antarest.launcher.adapters.slurm_launcher.batch_job import BatchJobManager
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers


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
    stats = [(5, 5, 1), (5, 5, 2), (5, 5, 3)]
    res = BatchJobManager.merge_std_deviation(stats)
    # todo this fails on purpose just to remember to create some real test
    assert len(res) == 1
