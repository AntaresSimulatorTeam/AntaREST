# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import re

import numpy as np
import pytest

from antarest.core.exceptions import GemsDuplicatedDataSeriesId
from antarest.study.business.model.gems.data_series import GemsDataSeries
from antarest.study.dao.api.study_dao import StudyDao


def assert_data_series_equal(actual: list[GemsDataSeries], expected: list[GemsDataSeries]) -> None:
    """`GemsDataSeries` can't be compared with `==` since its `values` field is a numpy array,
    whose own `==` returns an element-wise array rather than a bool."""
    actual_by_id = sorted(actual, key=lambda ds: ds.id)
    expected_by_id = sorted(expected, key=lambda ds: ds.id)
    assert [ds.id for ds in actual_by_id] == [ds.id for ds in expected_by_id]
    for a, e in zip(actual_by_id, expected_by_id):
        assert np.array_equal(a.values, e.values)


def test_default_case(dao_10_2: StudyDao) -> None:
    # We should not have any data series for default studies.
    assert dao_10_2.get_data_series() == []


def test_data_series_roundtrip(dao_10_2: StudyDao) -> None:
    load = GemsDataSeries(id="max_load_values", values=np.array([[10.0], [12.0], [14.0]]))
    wind = GemsDataSeries(id="wind_profile", values=np.array([[1.5, 2.5], [3.5, 4.5]]))

    dao_10_2.save_data_series([load, wind])
    assert_data_series_equal(dao_10_2.get_data_series(), [load, wind])

    # Saving again fully replaces the previous content, not merges with it.
    solar = GemsDataSeries(id="solar_profile", values=np.array([[0.1, 0.2, 0.3]]))
    dao_10_2.save_data_series([solar])
    assert_data_series_equal(dao_10_2.get_data_series(), [solar])

    # An empty batch clears all data series.
    dao_10_2.save_data_series([])
    assert dao_10_2.get_data_series() == []


def test_duplicate_ids_in_batch_keep_the_last_occurrence(dao_10_2: StudyDao) -> None:
    data_series = [
        GemsDataSeries(id="ds1", values=np.array([[1.0]])),
        GemsDataSeries(id="ds2", values=np.array([[1.0]])),
        GemsDataSeries(id="ds3", values=np.array([[1.0]])),
        GemsDataSeries(id="ds1", values=np.array([[2.0]])),
        GemsDataSeries(id="ds3", values=np.array([[1.0]])),
        GemsDataSeries(id="ds4", values=np.array([[1.0]])),
    ]

    with pytest.raises(GemsDuplicatedDataSeriesId, match=re.escape("Duplicated data series IDs: ['ds1', 'ds3']")):
        dao_10_2.save_data_series(data_series)

    assert dao_10_2.get_data_series() == []


def test_values_precision_is_preserved(dao_10_2: StudyDao) -> None:
    # Values that are not exactly representable with a naive, short decimal conversion (e.g.
    # `0.1 + 0.2`) must still come back bit-for-bit identical after a save/load roundtrip.
    tricky = GemsDataSeries(id="tricky", values=np.array([[0.1 + 0.2, 1 / 3, -42.0]]))

    dao_10_2.save_data_series([tricky])

    [loaded] = dao_10_2.get_data_series()
    assert np.array_equal(loaded.values, tricky.values)


def test_single_column_and_multi_column_series_coexist(dao_10_2: StudyDao) -> None:
    single_column = GemsDataSeries(id="single_column", values=np.array([[1.0], [2.0], [3.0]]))
    multi_column = GemsDataSeries(id="multi_column", values=np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]))

    dao_10_2.save_data_series([single_column, multi_column])

    assert_data_series_equal(dao_10_2.get_data_series(), [single_column, multi_column])
