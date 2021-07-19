import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import IO, Optional, Union
from uuid import uuid4

from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)

from antarest.core.utils.utils import extract_zip
from antarest.study.model import Study, RawStudy
from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
)
from antarest.core.exceptions import (
    BadOutputError,
    StudyValidationError,
)

logger = logging.getLogger(__name__)


class ImporterService:
    """
    Import zip study or just output folder
    """

    def __init__(
        self,
        study_service: RawStudyService,
        study_factory: StudyFactory,
    ):
        self.study_service = study_service
        self.study_factory = study_factory

    def import_study(self, metadata: RawStudy, stream: IO[bytes]) -> Study:
        """
        Import study
        Args:
            metadata: study information
            stream: study content compressed in zip file

        Returns: new study information.

        """
        path_study = self.study_service.get_study_path(metadata)
        path_study.mkdir()

        try:
            extract_zip(stream, path_study)
            fix_study_root(path_study)
            self.study_service.update_from_raw_meta(metadata)

        except Exception as e:
            shutil.rmtree(path_study)
            raise e

        metadata.path = str(path_study)
        return metadata

    def import_output(
        self, metadata: Study, output: Union[IO[bytes], Path]
    ) -> Optional[str]:
        """
        Import additional output on a existing study
        Args:
            metadata: study
            output: new output (path or zipped data)

        Returns: output id
        """
        path_output = (
            self.study_service.get_study_path(metadata)
            / "output"
            / f"imported_output_{str(uuid4())}"
        )
        os.makedirs(path_output)
        output_name: Optional[str] = None
        try:
            if isinstance(output, Path):
                if output != path_output:
                    shutil.copytree(output, path_output / "imported")
            else:
                extract_zip(output, path_output)

            fix_study_root(path_output)

            ini_reader = IniReader()
            info_antares_output = ini_reader.read(
                path_output / "info.antares-output"
            )["general"]

            date = datetime.fromtimestamp(
                int(info_antares_output["timestamp"])
            ).strftime("%Y%m%d-%H%M")

            mode = "eco" if info_antares_output["mode"] == "Economy" else "adq"
            name = (
                f"-{info_antares_output['name']}"
                if info_antares_output["name"]
                else ""
            )

            output_name = f"{date}{mode}{name}"
            path_output.rename(Path(path_output.parent, output_name))

            data = self.study_service.get(
                metadata,
                f"output/{output_name}",
                -1,
            )

            if data is None:
                self.study_service.delete_output(metadata, "imported_output")
                raise BadOutputError("The output provided is not conform.")

        except Exception as e:
            logger.error("Failed to import output", exc_info=e)
            shutil.rmtree(path_output)

        return output_name


def fix_study_root(study_path: Path) -> None:
    """
    Fix possibly the wrong study root on zipped archive (when the study root is nested)

    @param study_path the study initial root path
    """
    if not study_path.is_dir():
        raise StudyValidationError("Not a directory")

    root_path = study_path
    contents = os.listdir(root_path)
    sub_root_path = None
    while len(contents) == 1 and (root_path / contents[0]).is_dir():
        new_root = root_path / contents[0]
        if sub_root_path is None:
            sub_root_path = root_path / str(uuid4())
            shutil.move(str(new_root), str(sub_root_path))
            new_root = sub_root_path

        logger.debug(f"Searching study root in {new_root}")
        root_path = new_root
        if not new_root.is_dir():
            raise StudyValidationError("Not a directory")
        contents = os.listdir(new_root)

    if sub_root_path is not None:
        for item in os.listdir(root_path):
            shutil.move(str(root_path / item), str(study_path))
        shutil.rmtree(sub_root_path)
