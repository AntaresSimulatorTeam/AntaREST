from pathlib import Path
from typing import cast
from unittest.mock import patch, Mock

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
    res = BatchJobManager.merge_std_deviation(
        [
            (sub_set_means[i], subset_variances[i], len(subsets[i]))
            for i in range(0, 3)
        ]
    )
    assert f"{res[0]:.8f}" == f"{variance:.8f}"
    assert f"{res[1]:.8f}" == f"{mean:.8f}"
