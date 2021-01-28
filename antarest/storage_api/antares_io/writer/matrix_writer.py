import shutil
from pathlib import Path


class MatrixWriter:
    def write(self, matrix_path: Path, destination_path: Path) -> None:
        if matrix_path != destination_path:
            shutil.copyfile(matrix_path, destination_path)
