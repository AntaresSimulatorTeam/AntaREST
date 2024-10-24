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

import pytest

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.utils.archives import read_in_zip
from antarest.core.utils.utils import concat_files, concat_files_to_str, retry, suppress_exception


def test_retry() -> None:
    def func_failure() -> str:
        raise ShouldNotHappenException()

    with pytest.raises(ShouldNotHappenException):
        retry(func_failure, 2)


def test_concat_files(tmp_path: Path) -> None:
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f3 = tmp_path / "f3.txt"
    f_target = tmp_path / "f_target.txt"
    f1.write_text("hello")
    f2.write_text(" world !\n")
    f3.write_text("Done.")
    concat_files([f1, f2, f3], f_target)
    assert f_target.read_text(encoding="utf-8") == "hello world !\nDone."


def test_concat_files_to_str(tmp_path: Path) -> None:
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f3 = tmp_path / "f3.txt"
    f1.write_text("hello")
    f2.write_text(" world !\n")
    f3.write_text("Done.")
    assert concat_files_to_str([f1, f2, f3]) == "hello world !\nDone."


def test_read_in_zip(tmp_path: Path) -> None:
    zip_file = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as output_data:
        output_data.writestr("matrix.txt", "0\n1")
        output_data.writestr("sub/matrix2.txt", "0\n2")

    expected_results = []
    for file in ["matrix.txt", "sub/matrix2.txt", "missing.txt"]:
        read_in_zip(
            zip_file,
            Path(file),
            lambda p: expected_results.append(p.read_text(encoding="utf-8") if p else None),
        )

    assert expected_results[0] == "0\n1"
    assert expected_results[1] == "0\n2"
    assert expected_results[2] is None


def test_suppress_exception() -> None:
    def func_failure() -> str:
        raise ShouldNotHappenException()

    caught_exc = []
    suppress_exception(func_failure, lambda ex: caught_exc.append(ex))
    assert len(caught_exc) == 1
