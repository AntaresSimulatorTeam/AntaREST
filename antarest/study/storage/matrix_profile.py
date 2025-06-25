# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import copy
import fnmatch
from pathlib import Path
from typing import Dict, NamedTuple, Sequence

import pandas as pd
from antares.study.version import StudyVersion

from antarest.study.model import STUDY_VERSION_8_2, STUDY_VERSION_8_6, STUDY_VERSION_8_7
from antarest.study.storage.utils import MONTHS


class _MatrixProfile(NamedTuple):
    """
    Matrix profile for time series or specific matrices.
    """

    cols: Sequence[str]
    rows: Sequence[str]

    def process_dataframe(
        self,
        df: pd.DataFrame,
        matrix_path: str,
        *,
        with_index: bool,
        with_header: bool,
    ) -> None:
        """
        Adjust the column names and index of a dataframe according to the matrix profile.

        *NOTE:* The modification is done in place.

        Args:
            df: The dataframe to process.
            matrix_path: The path of the matrix file, relative to the study directory.
            with_index: Whether to set the index of the dataframe.
            with_header: Whether to set the column names of the dataframe.
        """
        if with_header:
            if Path(matrix_path).parts[1] == "links":
                cols = self._process_links_columns(matrix_path)
            else:
                cols = self.cols
            if cols:
                df.columns = pd.Index(cols)
            else:
                df.columns = pd.Index([f"TS-{i}" for i in range(1, len(df.columns) + 1)])

        if with_index and self.rows:
            df.index = pd.Index(self.rows)

    def _process_links_columns(self, matrix_path: str) -> Sequence[str]:
        """Process column names specific to the links matrices."""
        path_parts = Path(matrix_path).parts
        area1_id = path_parts[2]
        area2_id = path_parts[3]
        result = list(self.cols)
        for k, col in enumerate(result):
            if col == "Hurdle costs direct":
                result[k] = f"{col} ({area1_id}->{area2_id})"
            elif col == "Hurdle costs indirect":
                result[k] = f"{col} ({area2_id}->{area1_id})"
        return result


_SPECIFIC_MATRICES: Dict[str, _MatrixProfile]
"""
The dictionary ``_SPECIFIC_MATRICES`` maps file patterns to ``_MatrixProfile`` objects,
representing non-time series matrices.
It's used in the `adjust_matrix_columns_index` method to fetch matrix profiles based on study versions.
"""


# noinspection SpellCheckingInspection
_SPECIFIC_MATRICES = {
    "input/hydro/common/capacity/creditmodulations_*": _MatrixProfile(
        cols=[str(i) for i in range(101)],
        rows=["Generating Power", "Pumping Power"],
    ),
    "input/hydro/common/capacity/maxpower_*": _MatrixProfile(
        cols=[
            "Generating Max Power (MW)",
            "Generating Max Energy (Hours at Pmax)",
            "Pumping Max Power (MW)",
            "Pumping Max Energy (Hours at Pmax)",
        ],
        rows=[],
    ),
    "input/hydro/common/capacity/reservoir_*": _MatrixProfile(
        # Values are displayed in % in the UI, but the actual values are in p.u. (per unit)
        cols=["Lev Low (p.u)", "Lev Avg (p.u)", "Lev High (p.u)"],
        rows=[],
    ),
    "input/hydro/common/capacity/waterValues_*": _MatrixProfile(
        cols=[f"{i}%" for i in range(101)],
        rows=[],
    ),
    "input/hydro/series/*/mod": _MatrixProfile(cols=[], rows=[]),
    "input/hydro/series/*/ror": _MatrixProfile(cols=[], rows=[]),
    "input/hydro/common/capacity/inflowPattern_*": _MatrixProfile(cols=["Inflow Pattern (X)"], rows=[]),
    "input/hydro/prepro/*/energy": _MatrixProfile(
        cols=["Expectation (MWh)", "Std Deviation (MWh)", "Min. (MWh)", "Max. (MWh)", "ROR Share"],
        rows=list(MONTHS.keys()),
    ),
    "input/thermal/prepro/*/*/modulation": _MatrixProfile(
        cols=["Marginal cost modulation", "Market bid modulation", "Capacity modulation", "Min gen modulation"],
        rows=[],
    ),
    "input/thermal/prepro/*/*/data": _MatrixProfile(
        cols=["FO Duration", "PO Duration", "FO Rate", "PO Rate", "NPO Min", "NPO Max"],
        rows=[],
    ),
    "input/reserves/*": _MatrixProfile(
        cols=["Primary Res. (draft)", "Strategic Res. (draft)", "DSM", "Day Ahead"],
        rows=[],
    ),
    "input/misc-gen/miscgen-*": _MatrixProfile(
        cols=["CHP", "Bio Mass", "Bio Gaz", "Waste", "GeoThermal", "Other", "PSP", "ROW Balance"],
        rows=[],
    ),
    "input/bindingconstraints/*": _MatrixProfile(cols=["<", ">", "="], rows=[]),
    "input/links/*/*": _MatrixProfile(
        cols=[
            "Capacités de transmission directes",
            "Capacités de transmission indirectes",
            "Hurdle costs direct",
            "Hurdle costs indirect",
            "Impedances",
            "Loop flow",
            "P.Shift Min",
            "P.Shift Max",
        ],
        rows=[],
    ),
}

_SPECIFIC_MATRICES_8_2 = copy.deepcopy(_SPECIFIC_MATRICES)
"""Specific matrices for study version 8.2."""

_SPECIFIC_MATRICES_8_2["input/links/*/*"] = _MatrixProfile(
    cols=[
        "Hurdle costs direct",
        "Hurdle costs indirect",
        "Impedances",
        "Loop flow",
        "P.Shift Min",
        "P.Shift Max",
    ],
    rows=[],
)

# Specific matrices for study version 8.6
_SPECIFIC_MATRICES_8_6 = copy.deepcopy(_SPECIFIC_MATRICES_8_2)
"""Specific matrices for study version 8.6."""

# noinspection SpellCheckingInspection
#
_SPECIFIC_MATRICES_8_6["input/hydro/series/*/mingen"] = _MatrixProfile(cols=[], rows=[])

_SPECIFIC_MATRICES_8_7 = copy.deepcopy(_SPECIFIC_MATRICES_8_2)
"""Specific matrices for study version 8.7."""

# noinspection SpellCheckingInspection
# Scenarized RHS for binding constraints
_SPECIFIC_MATRICES_8_7["input/bindingconstraints/*"] = _MatrixProfile(cols=[], rows=[])


def adjust_matrix_columns_index(
    df: pd.DataFrame, matrix_path: str, with_index: bool, with_header: bool, study_version: StudyVersion
) -> None:
    """
    Adjust the column names and index of a dataframe according to the matrix profile.

    *NOTE:* The modification is done in place.

    Args:
        df: The dataframe to process.
        matrix_path: The path of the matrix file, relative to the study directory.
        with_index: Whether to set the index of the dataframe.
        with_header: Whether to set the column names of the dataframe.
        study_version: The version of the study.
    """
    # Get the matrix profiles for a given study version
    if study_version < STUDY_VERSION_8_2:
        matrix_profiles = _SPECIFIC_MATRICES
    elif study_version < STUDY_VERSION_8_6:
        matrix_profiles = _SPECIFIC_MATRICES_8_2
    elif study_version < STUDY_VERSION_8_7:
        matrix_profiles = _SPECIFIC_MATRICES_8_6
    else:
        matrix_profiles = _SPECIFIC_MATRICES_8_7

    # Apply the matrix profile to the dataframe to adjust the column names and index
    for pattern, matrix_profile in matrix_profiles.items():
        if fnmatch.fnmatch(matrix_path, pattern):
            matrix_profile.process_dataframe(
                df,
                matrix_path,
                with_index=with_index,
                with_header=with_header,
            )
            return

    if fnmatch.fnmatch(matrix_path, "output/*"):
        # Outputs already have their own column names
        return

    # The matrix may be a time series, in which case we don't need to adjust anything
    # (the "Time" columns is already the index)
    # Column names should be Monte-Carlo years: "TS-1", "TS-2", ...
    df.columns = pd.Index([f"TS-{i}" for i in range(1, len(df.columns) + 1)])

    return None
