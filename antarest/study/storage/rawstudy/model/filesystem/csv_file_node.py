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
from pathlib import Path
from typing import Any

import polars as pl


class CsvReader:
    """
    CSV file reader.
    """

    @staticmethod
    def read(path: Any) -> pl.DataFrame:

        if isinstance(path, (Path, str)):
            try:
                return pl.read_csv(path)

            except FileNotFoundError:
                return pl.DataFrame()

        else:  # pragma: no cover
            raise TypeError(repr(type(path)))


class CsvWriter:
    """
    CSV file writer.
    """

    @staticmethod
    def write(data: pl.DataFrame, path: Path) -> None:
        data.write_csv(path)
