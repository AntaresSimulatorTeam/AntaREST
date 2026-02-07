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

import shutil
import zipfile
from pathlib import Path

import py7zr
import pytest

from antarest.core.exceptions import BadArchiveContent, ShouldNotHappenException
from antarest.core.utils import archives
from antarest.core.utils.archives import ArchiveFormat, archive_dir, extract_archive_from_path, unzip


def _create_sample_dir(base: Path) -> Path:
    src = base / "study"
    src.mkdir()
    (src / "input").mkdir()
    (src / "input" / "data.txt").write_text("hello")
    (src / "settings.ini").write_text("key=value")
    return src


def _assert_archive_contains_sample_files(names: set[str]) -> None:
    assert any(n.endswith("input/data.txt") for n in names)
    assert any(n.endswith("settings.ini") for n in names)


class TestArchiveDir:
    def test_zip_creates_valid_archive(self, tmp_path: Path) -> None:
        src = _create_sample_dir(tmp_path)
        archive_path = tmp_path / "output.zip"

        archive_dir(src, archive_path)

        assert archive_path.exists()
        with zipfile.ZipFile(archive_path) as zf:
            _assert_archive_contains_sample_files(set(zf.namelist()))

    def test_7z_calls_cli_when_available(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        src = _create_sample_dir(tmp_path)
        archive_path = tmp_path / "output.7z"
        run_calls = []

        monkeypatch.setattr(archives, "_has_7z", lambda: True)
        monkeypatch.setattr(archives, "run", lambda *a, **kw: run_calls.append((a, kw)))

        archive_dir(src, archive_path, archive_format=ArchiveFormat.SEVEN_ZIP)

        assert len(run_calls) == 1

    def test_7z_uses_py7zr_when_cli_unavailable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        src = _create_sample_dir(tmp_path)
        archive_path = tmp_path / "output.7z"
        run_calls = []

        monkeypatch.setattr(archives, "_has_7z", lambda: False)
        monkeypatch.setattr(archives, "run", lambda *a, **kw: run_calls.append((a, kw)))

        archive_dir(src, archive_path, archive_format=ArchiveFormat.SEVEN_ZIP)

        assert len(run_calls) == 0
        assert archive_path.exists()
        with py7zr.SevenZipFile(archive_path) as szf:
            _assert_archive_contains_sample_files(set(szf.getnames()))

    def test_remove_source_dir(self, tmp_path: Path) -> None:
        src = _create_sample_dir(tmp_path)
        archive_path = tmp_path / "output.zip"

        archive_dir(src, archive_path, remove_source_dir=True)

        assert archive_path.exists()
        assert not src.exists()

    def test_mismatched_format_raises(self, tmp_path: Path) -> None:
        src = _create_sample_dir(tmp_path)
        archive_path = tmp_path / "output.zip"

        with pytest.raises(ShouldNotHappenException):
            archive_dir(src, archive_path, archive_format=ArchiveFormat.SEVEN_ZIP)

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        src = _create_sample_dir(tmp_path)
        archive_path = tmp_path / "output.tar.gz"

        with pytest.raises(ShouldNotHappenException):
            archive_dir(src, archive_path)


def _create_sample_archive_7z(base: Path) -> Path:
    """Create a sample .7z archive using py7zr for testing."""
    src = _create_sample_dir(base)
    archive_path = base / "test.7z"
    with py7zr.SevenZipFile(archive_path, mode="w") as szf:
        szf.writeall(src, arcname="")
    shutil.rmtree(src)
    return archive_path


def _create_sample_archive_zip(base: Path) -> Path:
    """Create a sample .zip archive using zipfile for testing."""
    src = _create_sample_dir(base)
    archive_path = base / "test.zip"
    with zipfile.ZipFile(archive_path, mode="w") as zf:
        for root, _, files in __import__("os").walk(src):
            for file in files:
                file_path = Path(root) / file
                zf.write(file_path, file_path.relative_to(src))
    shutil.rmtree(src)
    return archive_path


def _assert_extracted_sample_files(target_dir: Path) -> None:
    assert (target_dir / "input" / "data.txt").read_text() == "hello"
    assert (target_dir / "settings.ini").read_text() == "key=value"


class TestExtractArchiveFromPath:
    def test_7z_calls_cli_when_available(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        archive_path = _create_sample_archive_7z(tmp_path)
        target_dir = tmp_path / "output"
        target_dir.mkdir()
        run_calls = []

        monkeypatch.setattr(archives, "_has_7z", lambda: True)
        monkeypatch.setattr(archives, "run", lambda *a, **kw: run_calls.append((a, kw)))

        extract_archive_from_path(archive_path, target_dir)

        assert len(run_calls) == 1
        args = run_calls[0][0][0]
        assert args[0] == "7z"
        assert args[1] == "x"
        assert str(archive_path) in args[2]
        assert f"-o{target_dir}" in args[3]

    def test_7z_uses_py7zr_when_cli_unavailable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        archive_path = _create_sample_archive_7z(tmp_path)
        target_dir = tmp_path / "output"
        target_dir.mkdir()

        monkeypatch.setattr(archives, "_has_7z", lambda: False)

        extract_archive_from_path(archive_path, target_dir)

        _assert_extracted_sample_files(target_dir)

    def test_zip_calls_cli_when_available(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        archive_path = _create_sample_archive_zip(tmp_path)
        target_dir = tmp_path / "output"
        target_dir.mkdir()
        run_calls = []

        monkeypatch.setattr(archives, "_has_7z", lambda: True)
        monkeypatch.setattr(archives, "run", lambda *a, **kw: run_calls.append((a, kw)))

        extract_archive_from_path(archive_path, target_dir)

        assert len(run_calls) == 1

    def test_zip_uses_zipfile_when_cli_unavailable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        archive_path = _create_sample_archive_zip(tmp_path)
        target_dir = tmp_path / "output"
        target_dir.mkdir()

        monkeypatch.setattr(archives, "_has_7z", lambda: False)

        extract_archive_from_path(archive_path, target_dir)

        _assert_extracted_sample_files(target_dir)

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        archive_path = tmp_path / "test.tar.gz"
        archive_path.write_bytes(b"dummy")
        target_dir = tmp_path / "output"
        target_dir.mkdir()

        with pytest.raises(BadArchiveContent):
            extract_archive_from_path(archive_path, target_dir)


class TestUnzip:
    def test_unzip_calls_cli_when_available(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        archive_path = _create_sample_archive_zip(tmp_path)
        target_dir = tmp_path / "output"
        target_dir.mkdir()
        run_calls = []

        monkeypatch.setattr(archives, "_has_7z", lambda: True)
        monkeypatch.setattr(archives, "run", lambda *a, **kw: run_calls.append((a, kw)))

        unzip(target_dir, archive_path)

        assert len(run_calls) == 1
        assert not archive_path.exists()

    def test_unzip_uses_zipfile_when_cli_unavailable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        archive_path = _create_sample_archive_zip(tmp_path)
        target_dir = tmp_path / "output"
        target_dir.mkdir()

        monkeypatch.setattr(archives, "_has_7z", lambda: False)

        unzip(target_dir, archive_path)

        _assert_extracted_sample_files(target_dir)
        assert not archive_path.exists()
