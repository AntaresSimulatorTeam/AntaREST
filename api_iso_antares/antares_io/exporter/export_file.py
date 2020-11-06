import glob
import os
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


class Exporter:
    def export_file(self, path_study: Path) -> BytesIO:
        data = BytesIO()
        zipf = ZipFile(data, "w", ZIP_DEFLATED)
        root = path_study.name + os.sep
        root_abs = path_study.absolute()
        os.chdir(path_study)
        a = glob.glob("**", recursive=True)
        for path in a:
            zipf.write(root_abs / path, root + path)
        zipf.close()
        data.seek(0)
        return data
