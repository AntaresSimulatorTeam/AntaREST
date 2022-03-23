from pathlib import Path
from unittest.mock import patch, Mock

from antarest.launcher.adapters.slurm_launcher.batch_job import BatchJobManager
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers


@patch.object(FileStudyHelpers, "get_playlist")
def test_batch_compute_params(get_playlist_mock):
    batch_job_manager = BatchJobManager("workspace", Mock(), Mock())
    playlist = [year for year in range(0, 102)]
    get_playlist_mock.return_value = playlist
    batch = batch_job_manager.compute_batch_params(
        Path("some path"), "some id"
    )
    assert len(batch) == 2
    assert batch[1] == [100, 101]

    playlist = [year for year in range(0, 100)]
    get_playlist_mock.return_value = playlist
    batch = batch_job_manager.compute_batch_params(
        Path("some path"), "some id"
    )
    assert len(batch) == 1

    playlist = [year for year in range(0, 200)]
    get_playlist_mock.return_value = playlist
    batch = batch_job_manager.compute_batch_params(
        Path("some path"), "some id"
    )
    assert len(batch) == 2
    assert len(batch[1]) == 100
