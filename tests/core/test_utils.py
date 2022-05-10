from pathlib import Path

import pytest

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.utils.utils import retry, concat_files


def test_retry():
    def func_failure() -> str:
        raise ShouldNotHappenException()

    with pytest.raises(ShouldNotHappenException):
        retry(func_failure, 2)


def test_concat_files(tmp_path: Path):
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f3 = tmp_path / "f3.txt"
    f_target = tmp_path / "f_target.txt"
    f1.write_text("hello")
    f2.write_text(" world !\n")
    f3.write_text("Done.")
    concat_files([f1, f2, f3], f_target)
    assert f_target.read_text(encoding="utf-8") == "hello world !\nDone."
