# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import py7zr
import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.exceptions import SimulationParsingError
from antarest.study.storage.rawstudy.model.filesystem.config.files import parse_simulation_archive
from antarest.study.storage.rawstudy.model.filesystem.config.model import Simulation

PARSE_SIMULATION_NAME = "antarest.study.storage.rawstudy.model.filesystem.config.files.parse_simulation"


class TestParseSimulationZip:
    def test_parse_simulation_archive__nominal_zip(self, tmp_path: Path):
        # prepare a ZIP file with the following files
        archived_files = [
            "about-the-study/parameters.ini",
            "expansion/out.json",
            "checkIntegrity.txt",
        ]
        zip_path = tmp_path.joinpath("dummy.zip")
        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name in archived_files:
                zf.writestr(name, b"dummy data")

        def my_parse_simulation(path: Path, canonical_name: str) -> Simulation:
            """
            Mock function of the function `parse_simulation`, which is used to:
            - avoid calling the original function which do a lot of stuff,
            - check that the required files exist in a temporary directory.
            """
            assert path.is_dir()
            assert canonical_name == zip_path.stem
            for name_ in archived_files:
                uncompressed = path.joinpath(name_)
                assert uncompressed.is_file(), f"Missing {name_}"
            return Mock(spec=Simulation)

        # Call the `parse_simulation_archive` but using `my_parse_simulation`
        with patch(PARSE_SIMULATION_NAME, new=my_parse_simulation):
            actual = parse_simulation_archive(zip_path)

        # check the result
        assert actual.archived is True

    def test_parse_simulation_archive__nominal_7z(self, tmp_path: Path):
        # prepare a ZIP file with the following files
        archived_files = [
            "about-the-study/parameters.ini",
            "expansion/out.json",
            "checkIntegrity.txt",
        ]
        archive_path = tmp_path.joinpath("dummy.7z")
        with py7zr.SevenZipFile(archive_path, mode="w") as zf:
            for name in archived_files:
                zf.writestr(b"dummy data", name)

        def my_parse_simulation(path: Path, canonical_name: str) -> Simulation:
            """
            Mock function of the function `parse_simulation`, which is used to:
            - avoid calling the original function which do a lot of stuff,
            - check that the required files exist in a temporary directory.
            """
            assert path.is_dir()
            assert canonical_name == archive_path.stem
            for name_ in archived_files:
                uncompressed = path.joinpath(name_)
                assert uncompressed.is_file(), f"Missing {name_}"
            return Mock(spec=Simulation)

        # Call the `parse_simulation_archive` but using `my_parse_simulation`
        with patch(PARSE_SIMULATION_NAME, new=my_parse_simulation):
            actual = parse_simulation_archive(archive_path)

        # check the result
        assert actual.archived is True

    def test_parse_simulation_archive__missing_required_files(self, tmp_path: Path):
        # prepare a ZIP file with the following files
        archived_files = [
            # "about-the-study/parameters.ini",  # <- required
            "expansion/out.json",  # optional
            "checkIntegrity.txt",  # optional
        ]
        zip_path = tmp_path.joinpath("dummy.zip")
        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name in archived_files:
                zf.writestr(name, b"dummy data")

        # Call the `parse_simulation_archive` but using `my_parse_simulation`
        with patch(PARSE_SIMULATION_NAME):
            with pytest.raises(SimulationParsingError):
                parse_simulation_archive(zip_path)

    def test_parse_simulation_archive__bad_zip_file(self, tmp_path: Path):
        # prepare a bad ZIP file
        zip_path = tmp_path.joinpath("dummy.zip")
        zip_path.write_bytes(b"PK")

        # Call the `parse_simulation_archive` but using `my_parse_simulation`
        with patch(PARSE_SIMULATION_NAME):
            with pytest.raises(SimulationParsingError):
                parse_simulation_archive(zip_path)
