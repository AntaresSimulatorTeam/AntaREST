from pathlib import Path
from time import time
from typing import Callable, Any
from zipfile import ZipFile

from api_iso_antares.filesystem.factory import StudyFactory


def extract_sta(tmp_path: Path, project_path: Path) -> Path:
    path_studies = Path(tmp_path) / "studies"

    sta_mini_zip_path = project_path / "examples/studies/STA-mini.zip"

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    return path_studies / "STA-mini"


def benchmark(function: Callable) -> [Any, float]:
    bench = time()
    res = function()
    bench = time() - bench
    return res, bench


def test_performance(tmp_path: Path, project_path: Path):

    path_studies = extract_sta(tmp_path, project_path)

    bench = {"build": 0}

    (_, study), bench["build"] = benchmark(
        lambda: StudyFactory().create_from_fs(path_studies)
    )
    data, bench["get"] = benchmark(lambda: study.get())
    _, bench["get_version"] = benchmark(
        lambda: study.get(["study", "antares", "author"])
    )

    _, bench["save"] = benchmark(lambda: study.save(data))
    _, bench["save_author"] = benchmark(
        lambda: study.save("John Smith", url=["study", "antares", "author"])
    )
    print(bench)
