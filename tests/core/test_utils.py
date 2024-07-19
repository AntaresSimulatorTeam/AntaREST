import zipfile
from pathlib import Path

import py7zr
import pytest

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.utils.utils import concat_files, concat_files_to_str, read_in_zip, retry, suppress_exception


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


@pytest.mark.parametrize("archive_name", ["test.zip", "test.7z"])
def test_read_in_zip(tmp_path: Path, archive_name: str) -> None:
    archive_file = tmp_path.joinpath(archive_name)

    inner_files = {
        "matrix.txt": "0\n1",
        "sub/matrix2.txt": "0\n2",
    }

    if archive_file.suffix == ".zip":
        with zipfile.ZipFile(archive_file, "w", zipfile.ZIP_DEFLATED) as archive_zip:
            for relpath, content in inner_files.items():
                archive_zip.writestr(relpath, content)
    elif archive_file.suffix == ".7z":
        with py7zr.SevenZipFile(archive_file, "w") as archive_7z:
            for relpath, content in inner_files.items():
                archive_7z.writestr(content, relpath)
    else:
        raise NotImplementedError(f"Unknown suffix {archive_file.suffix}")

    actual_files = {}

    def read_result(rp: str, p: Path) -> None:
        actual_files[rp] = p.read_text(encoding="utf-8") if p else None

    for relpath in ["matrix.txt", "sub/matrix2.txt", "missing.txt"]:
        read_in_zip(archive_file, Path(relpath), lambda p: read_result(relpath, p))

    expected = {**inner_files, "missing.txt": None}
    assert actual_files == expected


def test_suppress_exception() -> None:
    def func_failure() -> str:
        raise ShouldNotHappenException()

    caught_exc = []
    suppress_exception(func_failure, lambda ex: caught_exc.append(ex))
    assert len(caught_exc) == 1
