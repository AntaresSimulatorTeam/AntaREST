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
import csv
from pathlib import Path
from typing import Any

from typing_extensions import override

from antarest.core.serde.ini_reader import IReader
from antarest.core.serde.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class CsvReader(IReader):
    """
    CSV file reader.
    """

    @override
    def read(self, path: Any, **kwargs: Any) -> Any:
        rows: list[Any]

        if isinstance(path, (Path, str)):
            try:
                with Path(path).open(encoding="utf-8", newline="") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
            except FileNotFoundError:
                # If the file is missing, an empty list is returned,
                # to mimic the behavior of `configparser.ConfigParser`.
                return []

        else:  # pragma: no cover
            raise TypeError(repr(type(path)))

        try:
            return rows
        except csv.Error as exc:
            err_msg = f"Failed to parse CSV file '{path}'"
            raise ValueError(err_msg) from exc


class CsvWriter(IniWriter):
    """
    CSV file writer.
    """

    @override
    def write(self, data: dict[str, Any], path: Path) -> None:
        rows = [list(data.keys())] + list(zip(*data.values()))
        self.write_rows(rows, path)

    @staticmethod
    def write_rows(data: list[Any], path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerows(data)


class CsvFileNode(IniFileNode):
    def __init__(self, config: FileStudyTreeConfig) -> None:
        super().__init__(config, CsvReader(), CsvWriter())
