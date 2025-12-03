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
from enum import Enum, StrEnum
from pathlib import Path
from typing import TypeAlias

import pandas as pd

from antarest.study.storage.rawstudy.model.filesystem.matrix.date_serializer import (
    FactoryDateSerializer,
    rename_unnamed,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency

"""Column name for the Monte Carlo year."""
MCYEAR_COL = "mcYear"


class MCRoot(Enum):
    MC_IND = "mc-ind"
    MC_ALL = "mc-all"


class MCIndAreasQueryFile(StrEnum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"


class MCAllAreasQueryFile(StrEnum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"
    ID = "id"


class MCIndLinksQueryFile(StrEnum):
    VALUES = "values"


class MCAllLinksQueryFile(StrEnum):
    VALUES = "values"
    ID = "id"


QueryFileType: TypeAlias = MCIndAreasQueryFile | MCAllAreasQueryFile | MCIndLinksQueryFile | MCAllLinksQueryFile


def parse_output_file(file_path: Path, frequency: MatrixFrequency, n_rows: int | None = None) -> pd.DataFrame:
    csv_file = pd.read_csv(
        file_path, sep="\t", skiprows=4, header=[0, 1, 2], na_values="N/A", float_precision="legacy", nrows=n_rows
    )
    date_serializer = FactoryDateSerializer.create(frequency.value, "")
    _, body = date_serializer.extract_date(csv_file)
    rename_unnamed(body)
    return body


def normalize_column_names(df: pd.DataFrame, mc_root: MCRoot) -> list[str]:
    new_cols = []
    for col in df.columns:
        if mc_root == MCRoot.MC_IND:
            name_to_consider = col[0]
        else:
            name_to_consider = " ".join([col[0], col[2]])
        new_cols.append(name_to_consider.upper().strip())
    return new_cols
