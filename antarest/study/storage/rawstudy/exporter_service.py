import glob
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from antarest.core.config import Config
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
)

logger = logging.getLogger(__name__)


class ExporterService:
    """
    Export study in zip format with or without output folder
    """

    def __init__(
        self,
        study_service: RawStudyService,
        study_factory: StudyFactory,
        config: Config,
    ):
        self.study_service = study_service
        self.study_factory = study_factory
        self.config = config

    def export_study(
        self, metadata: Study, target: Path, outputs: bool = True
    ) -> Path:
        """
        Export and compresse study inside zip
        Args:
            metadata: study
            target: path of the file to export to
            outputs: ask to integrated output folder inside exportation

        Returns: zip file with study files compressed inside

        """
        path_study = self.study_service.get_study_path(metadata)

        return self.export_file(path_study, target, outputs)

    def export_study_flat(
        self, metadata: Study, dest: Path, outputs: bool = True
    ) -> None:
        path_study = self.study_service.get_study_path(metadata)

        self.export_flat(path_study, dest, outputs)

    def export_file(
        self, path_study: Path, export_path: Path, outputs: bool = True
    ) -> Path:
        with tempfile.TemporaryDirectory(dir=self.config.tmp_dir) as tmpdir:
            tmp_study_path = Path(tmpdir) / "tmp_copy"
            self.export_flat(path_study, tmp_study_path, outputs)
            start_time = time.time()
            with ZipFile(export_path, "w", ZIP_DEFLATED) as zipf:
                current_dir = os.getcwd()
                os.chdir(tmp_study_path)

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
        stop_time = time.time()
        duration = "{:.3f}".format(stop_time - start_time)
        logger.info(f"Study {path_study} exported (flat mode) in {duration}s")
        _, study = self.study_factory.create_from_fs(dest, "")
        study.denormalize()
        duration = "{:.3f}".format(time.time() - stop_time)
        logger.info(f"Study {path_study} denormalized in {duration}s")
