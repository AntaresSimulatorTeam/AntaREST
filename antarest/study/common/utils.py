import logging
import tempfile
from pathlib import Path
from typing import Tuple, Any
from zipfile import ZipFile

logger = logging.getLogger(__name__)


def extract_file_to_tmp_dir(
    zip_path: Path, inside_zip_path: Path
) -> Tuple[Path, Any]:
    str_inside_zip_path = str(inside_zip_path).replace("\\", "/")
    tmp_dir = tempfile.TemporaryDirectory()
    with ZipFile(zip_path) as zip_obj:
        zip_obj.extract(str_inside_zip_path, tmp_dir.name)
    path = Path(tmp_dir.name) / inside_zip_path
    return path, tmp_dir
