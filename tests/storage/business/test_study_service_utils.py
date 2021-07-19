from hashlib import md5
from pathlib import Path
from zipfile import ZipFile

from antarest.storage.business.study_download_utils import StudyDownloader
from antarest.storage.model import MatrixAggregationResult, MatrixIndex


def test_output_downloads_export(tmp_path: Path):
    matrix = MatrixAggregationResult(
        index=MatrixIndex(),
        data={
            "a1": {
                "1": {
                    "A": [1, 2, 3, 4],
                    "B": [5, 6, 7, 8],
                },
                "2": {
                    "A": [10, 11, 12, 13],
                    "B": [14, None, None, 15],
                },
            },
            "a2": {
                "1": {
                    "A": [16, 17, 18, 19],
                    "B": [20, 21, 22, 23],
                },
                "2": {
                    "A": [24, None, 25, 26],
                    "B": [27, 28, 29, 30],
                },
            },
        },
        warnings=[],
    )
    zip_file = tmp_path / "output.zip"
    StudyDownloader.export(matrix, "application/zip", zip_file)
    with ZipFile(zip_file) as zip_input:
        assert zip_input.namelist() == ["a1.csv", "a2.csv"]
        assert (
            md5(zip_input.read("a1.csv")).hexdigest()
            == "eec20effc24b12284991f039f146fc9b"
        )
        assert (
            md5(zip_input.read("a2.csv")).hexdigest()
            == "f914fc39e32c3d02f491fed302513961"
        )
