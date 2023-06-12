import zipfile
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.exceptions import (
    SimulationParsingError,
)
from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    parse_simulation_zip,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Simulation,
)

PARSE_SIMULATION_NAME = "antarest.study.storage.rawstudy.model.filesystem.config.files.parse_simulation"


class TestParseSimulationZip:
    def test_parse_simulation_zip__nominal(self, tmp_path: Path):
        # prepare a ZIP file with the following files
        archived_files = [
            "about-the-study/parameters.ini",
            "expansion/out.json",
            "checkIntegrity.txt",
        ]
        zip_path = tmp_path.joinpath("dummy.zip")
        with zipfile.ZipFile(
            zip_path, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as zf:
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

        # Call the `parse_simulation_zip` but using `my_parse_simulation`
        with patch(PARSE_SIMULATION_NAME, new=my_parse_simulation):
            actual = parse_simulation_zip(zip_path)

        # check the result
        assert actual.archived is True

    def test_parse_simulation_zip__missing_required_files(
        self, tmp_path: Path
    ):
        # prepare a ZIP file with the following files
        archived_files = [
            # "about-the-study/parameters.ini",  # <- required
            "expansion/out.json",  # optional
            "checkIntegrity.txt",  # optional
        ]
        zip_path = tmp_path.joinpath("dummy.zip")
        with zipfile.ZipFile(
            zip_path, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as zf:
            for name in archived_files:
                zf.writestr(name, b"dummy data")

        # Call the `parse_simulation_zip` but using `my_parse_simulation`
        with patch(PARSE_SIMULATION_NAME):
            with pytest.raises(SimulationParsingError):
                parse_simulation_zip(zip_path)

    def test_parse_simulation_zip__bad_zip_file(self, tmp_path: Path):
        # prepare a bad ZIP file
        zip_path = tmp_path.joinpath("dummy.zip")
        zip_path.write_bytes(b"PK")

        # Call the `parse_simulation_zip` but using `my_parse_simulation`
        with patch(PARSE_SIMULATION_NAME):
            with pytest.raises(SimulationParsingError):
                parse_simulation_zip(zip_path)
