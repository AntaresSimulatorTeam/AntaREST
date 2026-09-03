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
from antarest.study.dao.api.common import remove_reserves_from_symmetries_dict


class TestRemoveReserveSymmetriesDictByCascade:
    """
    Cascade a reserve removal over every asset of an area.

    This is the only entry point in use, so it also covers the per-asset behaviour of
    `remove_reserve_symmetries_by_cascade`, which it delegates to.
    """

    def test_returns_none_when_nothing_changed(self) -> None:
        symmetries_dict = {"th1": [["r1", "r2"]]}

        assert remove_reserves_from_symmetries_dict(symmetries_dict, {"r9"}) is None
        assert symmetries_dict == {"th1": [["r1", "r2"]]}

    def test_a_set_applies_to_every_asset(self) -> None:
        symmetries_dict = {"th1": [["r1", "r2", "r3"]], "th2": [["r1", "r4"]]}

        result = remove_reserves_from_symmetries_dict(symmetries_dict, {"r1"})

        assert result == {"th1": [["r2", "r3"]], "th2": []}

    def test_a_dict_applies_per_asset(self) -> None:
        symmetries_dict = {"th1": [["r1", "r2", "r3"]], "th2": [["r1", "r2", "r3"]]}

        result = remove_reserves_from_symmetries_dict(symmetries_dict, {"th1": {"r1"}, "th2": {"r3"}})

        assert result == {"th1": [["r2", "r3"]], "th2": [["r1", "r2"]]}

    def test_an_asset_missing_from_the_dict_is_left_alone(self) -> None:
        symmetries_dict = {"th1": [["r1", "r2"]], "th2": [["r1", "r2"]]}

        result = remove_reserves_from_symmetries_dict(symmetries_dict, {"th1": {"r1"}})

        assert result == {"th1": [], "th2": [["r1", "r2"]]}

    def test_reports_a_change_on_any_asset_not_only_the_first(self) -> None:
        # Guards against short-circuiting: the first asset is untouched, the second is not.
        symmetries_dict = {"th1": [["r1", "r2"], ["r3", "r2"]], "th2": [["r3", "r4", "r5"]]}

        result = remove_reserves_from_symmetries_dict(symmetries_dict, {"r3"})

        assert result == {"th1": [["r1", "r2"]], "th2": [["r4", "r5"]]}

    def test_handles_an_empty_dict(self) -> None:
        assert remove_reserves_from_symmetries_dict({}, {"r1"}) is None

    def test_updates_every_symmetry_of_an_asset(self) -> None:
        # Guards the inner loop: an asset may hold several symmetries, all of them must be updated.
        symmetries_dict = {"th1": [["r1", "r2"], ["r1", "r3", "r4"], ["r5", "r6"]]}

        result = remove_reserves_from_symmetries_dict(symmetries_dict, {"r1"})

        # The first symmetry is left with a single reserve, so it is dropped instead of emptied.
        assert result == {"th1": [["r3", "r4"], ["r5", "r6"]]}

    def test_drops_a_symmetry_whose_reserves_are_all_removed(self) -> None:
        symmetries_dict = {"th1": [["r1", "r2"]]}

        result = remove_reserves_from_symmetries_dict(symmetries_dict, {"r1", "r2"})

        assert result == {"th1": []}

    def test_drops_symmetries_that_were_already_empty(self) -> None:
        # `[]` should never be stored, but a caller may still hand one over.
        symmetries_dict = {"th1": [[], ["r1", "r2"]]}

        result = remove_reserves_from_symmetries_dict(symmetries_dict, {"r1"})

        assert result == {"th1": []}

    def test_handles_an_asset_without_symmetries(self) -> None:
        symmetries_dict: dict[str, list[list[str]]] = {"th1": []}

        assert remove_reserves_from_symmetries_dict(symmetries_dict, {"r1"}) is None
        assert symmetries_dict == {"th1": []}

    def test_handles_an_empty_set_of_reserves(self) -> None:
        symmetries_dict = {"th1": [["r1", "r2"]]}

        assert remove_reserves_from_symmetries_dict(symmetries_dict, set()) is None
        assert symmetries_dict == {"th1": [["r1", "r2"]]}
