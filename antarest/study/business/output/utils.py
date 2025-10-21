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
from pathlib import Path

import pandas as pd

from antarest.study.storage.rawstudy.model.filesystem.matrix.date_serializer import (
    FactoryDateSerializer,
    rename_unnamed,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


def parse_output_file(file_path: Path, frequency: MatrixFrequency, n_rows: int | None = None) -> pd.DataFrame:
    csv_file = pd.read_csv(
        file_path, sep="\t", skiprows=4, header=[0, 1, 2], na_values="N/A", float_precision="legacy", nrows=n_rows
    )
    date_serializer = FactoryDateSerializer.create(frequency.value, "")
    _, body = date_serializer.extract_date(csv_file)
    rename_unnamed(body)
    return body
