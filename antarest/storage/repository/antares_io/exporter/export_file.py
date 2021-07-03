import glob
import json
import logging
import os
import re
import shutil
import time
import uuid
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from antarest.common.custom_types import JSON


logger = logging.getLogger(__name__)

# TODO merge with exporter service ?
class Exporter:
    def export_file(
        self, path_study: Path, export_path: Path, outputs: bool = True
    ) -> Path:
        start_time = time.time()
        with ZipFile(export_path, "w", ZIP_DEFLATED) as zipf:
            current_dir = os.getcwd()
            os.chdir(path_study)

            for path in glob.glob("**", recursive=True):
                if outputs or path.split(os.sep)[0] != "output":
                    zipf.write(path, path)

            zipf.close()

            os.chdir(current_dir)
        duration = "{:.3f}".format(time.time() - start_time)
        logger.info(
            f"Study {path_study} exported (zipped mode) in {duration}s"
        )
        return export_path

    def export_flat(
        self,
        path_study: Path,
        dest: Path,
        outputs: bool = False,
    ) -> None:
        start_time = time.time()
        ignore_patterns = (
            (
                lambda directory, contents: ["output"]
                if str(directory) == str(path_study)
                else []
            )
            if not outputs
            else None
        )
        shutil.copytree(src=path_study, dst=dest, ignore=ignore_patterns)
        duration = "{:.3f}".format(time.time() - start_time)
        logger.info(f"Study {path_study} exported (flat mode) in {duration}s")
