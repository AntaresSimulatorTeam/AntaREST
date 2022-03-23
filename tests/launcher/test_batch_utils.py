from unittest.mock import patch, Mock

from antarest.launcher.adapters.slurm_launcher.batch_job import BatchJobManager
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers


@patch.object(FileStudyHelpers, "get_playlist")
def test_batch_compute_params(get_playlist_mock):
    playlist = [year for year in range(0, 102)]
    get_playlist_mock.return_value = playlist
    batch = BatchJobManager.compute_batch_params(Mock())
    assert len(batch) == 2
    assert batch[1] == [100, 101]

    playlist = [year for year in range(0, 100)]
    get_playlist_mock.return_value = playlist
    batch = BatchJobManager.compute_batch_params(Mock())
    assert len(batch) == 1

    playlist = [year for year in range(0, 200)]
    get_playlist_mock.return_value = playlist
    batch = BatchJobManager.compute_batch_params(Mock())
    assert len(batch) == 2
    assert len(batch[1]) == 100
