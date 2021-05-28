from io import BytesIO
from pathlib import Path

from antarest.common.interfaces.eventbus import IEventBus
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

    def export_study(self, metadata: Study, outputs: bool = True) -> BytesIO:
        path_study = self.study_service.get_study_path(metadata)

        self.study_service.check_study_exists(metadata)

        return self.exporter.export_file(path_study, outputs)

    def get_matrix(self, metadata: Study, path: str) -> bytes:
        file = self.study_service.get_study_path(metadata) / path
        return file.read_bytes()
