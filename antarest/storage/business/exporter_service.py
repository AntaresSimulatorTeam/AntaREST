from io import BytesIO
from pathlib import Path

from antarest.storage.business.raw_study_service import RawStudyService
from antarest.storage.model import Study
from antarest.storage.repository.antares_io.exporter.export_file import (
    Exporter,
)
from antarest.storage.repository.filesystem.factory import StudyFactory


class ExporterService:
    """
    Export study in zip format with or without output folder
    """

    def __init__(
        self,
        study_service: RawStudyService,
        study_factory: StudyFactory,
        exporter: Exporter,
    ):
        self.study_service = study_service
        self.study_factory = study_factory
        self.exporter = exporter

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

        self.study_service.check_study_exists(metadata)

        return self.exporter.export_file(path_study, target, outputs)

    def export_study_flat(
        self, metadata: Study, dest: Path, outputs: bool = True
    ) -> None:
        path_study = self.study_service.get_study_path(metadata)

        self.study_service.check_study_exists(metadata)

        self.exporter.export_flat(path_study, dest, outputs)

    def get_matrix(self, metadata: Study, path: str) -> BytesIO:
        """
        Get matrix file content
        Args:
            metadata: study with matrix inside
            path: path inside study

        Returns: content file

        """
        file = self.study_service.get_study_path(metadata) / path
        return BytesIO(file.read_bytes())
