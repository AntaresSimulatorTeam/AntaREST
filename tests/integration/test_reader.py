from pathlib import Path

import pytest

from api_iso_antares.antares_io.reader import IniReader, StudyReader


@pytest.mark.integration_test
def test_reader_folder(tmp_path: str) -> None:

    """
    study1
    |
    _ file1.ini
    |_folder1
        |_ file2.ini
        |_ matrice1.txt
        |_ folder2
            |_ matrice2.txt
    |_folder3
        |_ file3.ini
    """

    str_content_ini = """
    [section]
    params = 123
    """

    path = Path(tmp_path) / "study1"
    path_study = Path(path)
    path.mkdir()
    (path / "file1.ini").write_text(str_content_ini)
    path /= "folder1"
    path.mkdir()
    (path / "file2.ini").write_text(str_content_ini)
    (path / "matrice1.txt").touch()
    path /= "folder2"
    path.mkdir()
    (path / "matrice2.txt").touch()
    path = Path(path_study) / "folder3"
    path.mkdir()
    (path / "file3.ini").write_text(str_content_ini)

    ini_content = {"section": {"params": 123}}

    study_reader = StudyReader(reader_ini=IniReader())

    expected_json = {
        "file1.ini": ini_content,
        "folder1": {
            "file2.ini": ini_content,
            "matrice1.txt": str(Path("matrices/study1/folder1/matrice1.txt")),
            "folder2": {
                "matrice2.txt": str(
                    Path("matrices/study1/folder1/folder2/matrice2.txt")
                ),
            },
        },
        "folder3": {"file3.ini": ini_content},
    }

    res = study_reader.read(path_study)
    assert res == expected_json
