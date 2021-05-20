import glob
import json
import os
import re
import uuid
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from antarest.common.custom_types import JSON


class Exporter:
    def export_file(self, path_study: Path, outputs: bool = True) -> BytesIO:
        data = BytesIO()
        zipf = ZipFile(data, "w", ZIP_DEFLATED)

        current_dir = os.getcwd()
        os.chdir(path_study)

        for path in glob.glob("**", recursive=True):
            if outputs or path.split(os.sep)[0] != "output":
                zipf.write(path, path)

        zipf.close()

        os.chdir(current_dir)
        data.seek(0)
        return data
