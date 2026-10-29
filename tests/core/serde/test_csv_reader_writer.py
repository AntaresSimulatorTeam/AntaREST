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

from polars import DataFrame

from antarest.study.storage.rawstudy.model.filesystem.csv_file_node import CsvReader, CsvWriter

csv_data = DataFrame(
    {
        "columnA": ["row1A", "row2A"],
        "columnB": ["row1B", "row2B"],
        "columnC": ["row1C", "row2C"],
    }
)

csv_data_dict = {"columnA": ["row1A", "row2A"], "columnB": ["row1B", "row2B"], "columnC": ["row1C", "row2C"]}


def test_behaviour_for_missing_file(tmp_path: Path) -> None:
    reader = CsvReader()
    empty_content = reader.read(tmp_path / "empty.csv")
    assert empty_content.equals(DataFrame())


def test_csv_reader_and_write_rows(tmp_path: Path) -> None:
    csv_file = tmp_path / "test.csv"

    # Ensures the writer can create a file that doesn't exist and write the data as it should.
    expected_content = """columnA,columnB,columnC
row1A,row1B,row1C
row2A,row2B,row2C
"""
    CsvWriter.write(csv_data, csv_file)
    content = csv_file.read_text()
    assert content == expected_content

    # Ensures the reader can read the data as it should.
    reader = CsvReader()
    parsed_content = reader.read(csv_file)
    assert parsed_content.equals(csv_data)
