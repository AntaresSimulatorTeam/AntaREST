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

import pytest

from antarest.output.utils import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    RawOutputMatrixQuery,
    parse_raw_output_matrix_path,
)
from antarest.study.model import MatrixFrequency


class TestParseRawOutputMatrixPath:
    def test_mc_all_areas_values(self) -> None:
        result = parse_raw_output_matrix_path(
            ["output", "20201014-1422eco", "economy", "mc-all", "areas", "fr", "values-hourly"]
        )
        assert result == RawOutputMatrixQuery(
            output_id="20201014-1422eco",
            query_file=MCAllAreasQueryFile.VALUES,
            frequency=MatrixFrequency.HOURLY,
            ids_to_consider=["fr"],
            mc_years=None,
        )

    def test_mc_all_areas_details(self) -> None:
        result = parse_raw_output_matrix_path(
            ["output", "20201014-1422eco", "economy", "mc-all", "areas", "de", "details-daily"]
        )
        assert result is not None
        assert result.query_file == MCAllAreasQueryFile.DETAILS
        assert result.frequency == MatrixFrequency.DAILY

    def test_mc_all_areas_details_st_storage(self) -> None:
        result = parse_raw_output_matrix_path(
            ["output", "20201014-1422eco", "economy", "mc-all", "areas", "fr", "details-STstorage-monthly"]
        )
        assert result is not None
        assert result.query_file == MCAllAreasQueryFile.DETAILS_ST_STORAGE
        assert result.frequency == MatrixFrequency.MONTHLY

    def test_mc_all_areas_details_res(self) -> None:
        result = parse_raw_output_matrix_path(
            ["output", "20201014-1422eco", "economy", "mc-all", "areas", "fr", "details-res-weekly"]
        )
        assert result is not None
        assert result.query_file == MCAllAreasQueryFile.DETAILS_RES
        assert result.frequency == MatrixFrequency.WEEKLY

    def test_mc_all_areas_id(self) -> None:
        result = parse_raw_output_matrix_path(
            ["output", "20201014-1422eco", "economy", "mc-all", "areas", "fr", "id-annual"]
        )
        assert result is not None
        assert result.query_file == MCAllAreasQueryFile.ID
        assert result.frequency == MatrixFrequency.ANNUAL

    def test_mc_all_links(self) -> None:
        result = parse_raw_output_matrix_path(
            ["output", "20201014-1422eco", "economy", "mc-all", "links", "fr", "de", "values-hourly"]
        )
        assert result == RawOutputMatrixQuery(
            output_id="20201014-1422eco",
            query_file=MCAllLinksQueryFile.VALUES,
            frequency=MatrixFrequency.HOURLY,
            ids_to_consider=["fr - de"],
            mc_years=None,
        )

    def test_mc_ind_areas(self) -> None:
        result = parse_raw_output_matrix_path(
            ["output", "20201014-1422eco", "economy", "mc-ind", "00001", "areas", "fr", "values-hourly"]
        )
        assert result == RawOutputMatrixQuery(
            output_id="20201014-1422eco",
            query_file=MCIndAreasQueryFile.VALUES,
            frequency=MatrixFrequency.HOURLY,
            ids_to_consider=["fr"],
            mc_years=[1],
        )

    def test_mc_ind_links(self) -> None:
        result = parse_raw_output_matrix_path(
            ["output", "20201014-1422eco", "economy", "mc-ind", "00042", "links", "fr", "de", "values-daily"]
        )
        assert result is not None
        assert result.query_file == MCIndLinksQueryFile.VALUES
        assert result.mc_years == [42]

    def test_adequacy_mode(self) -> None:
        result = parse_raw_output_matrix_path(
            ["output", "20201014-1422adq", "adequacy", "mc-all", "areas", "fr", "values-hourly"]
        )
        assert result is not None
        assert result.output_id == "20201014-1422adq"

    @pytest.mark.parametrize(
        "path_parts",
        [
            pytest.param([], id="empty"),
            pytest.param(["output"], id="output_only"),
            pytest.param(["output", "id"], id="too_short"),
            pytest.param(["output", "id", "economy", "mc-all", "areas", "fr"], id="missing_file_segment"),
            pytest.param(
                ["output", "id", "economy", "mc-ind", "areas", "fr", "values-hourly"],
                id="mc_ind_missing_year",
            ),
            pytest.param(["input", "id", "economy", "mc-all", "areas", "fr", "values-hourly"], id="not_output"),
            pytest.param(
                ["output", "id", "economy", "mc-all", "areas", "fr", "values"],
                id="no_frequency_separator",
            ),
            pytest.param(
                ["output", "id", "economy", "mc-all", "areas", "fr", "values-unknown"],
                id="invalid_frequency",
            ),
            pytest.param(
                ["output", "id", "economy", "mc-all", "areas", "fr", "unknown-hourly"],
                id="invalid_query_file",
            ),
            pytest.param(
                ["output", "id", "economy", "mc-all", "sets", "fr", "values-hourly"],
                id="invalid_area_or_link_type",
            ),
            pytest.param(
                ["output", "id", "economy", "mc-all", "links", "fr", "values-hourly"],
                id="link_missing_downstream",
            ),
            pytest.param(
                ["output", "id", "economy", "mc-ind", "notanumber", "areas", "fr", "values-hourly"],
                id="mc_ind_invalid_year",
            ),
            pytest.param(
                ["output", "id", "economy", "mc-ind", "00001", "links", "fr", "values-hourly"],
                id="mc_ind_link_missing_downstream",
            ),
            pytest.param(
                ["output", "id", "economy", "mc-other", "areas", "fr", "values-hourly"],
                id="invalid_mc_root",
            ),
            pytest.param(
                ["output", "id", "about-the-study", "parameters"],
                id="non_matrix_path",
            ),
            pytest.param(
                ["output", "id", "economy", "mc-all", "areas", "fr", "values-hourly", "extra"],
                id="mc_all_trailing_parts",
            ),
            pytest.param(
                ["output", "id", "economy", "mc-ind", "00001", "areas", "fr", "values-hourly", "extra"],
                id="mc_ind_trailing_parts",
            ),
        ],
    )
    def test_returns_none_for_invalid_paths(self, path_parts: list[str]) -> None:
        assert parse_raw_output_matrix_path(path_parts) is None

    @pytest.mark.parametrize("frequency", MatrixFrequency)
    def test_all_frequencies(self, frequency: MatrixFrequency) -> None:
        result = parse_raw_output_matrix_path(
            ["output", "id", "economy", "mc-all", "areas", "fr", f"values-{frequency.value}"]
        )
        assert result is not None
        assert result.frequency == frequency
