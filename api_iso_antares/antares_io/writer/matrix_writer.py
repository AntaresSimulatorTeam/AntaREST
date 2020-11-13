import shutil
from pathlib import Path


class MatrixWriter:
    def write(self, matrix_path: Path, destination_path: Path) -> None:
        shutil.copyfile(matrix_path, destination_path)
