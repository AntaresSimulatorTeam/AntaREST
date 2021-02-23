from io import BytesIO
from pathlib import Path

from antarest.storage.business.study_service import StudyService
from antarest.storage.repository.antares_io.exporter.export_file import (
    Exporter,
)
from antarest.storage.repository.filesystem.factory import StudyFactory


class ExporterService:
    def __init__(
        self,
        path_to_studies: Path,
        study_service: StudyService,
        study_factory: StudyFactory,
        exporter: Exporter,
    ):
        self.path_to_studies = path_to_studies
        self.study_service = study_service
        self.study_factory = study_factory
        self.exporter = exporter

    def export_study(
        self, name: str, compact: bool = False, outputs: bool = True
    ) -> BytesIO:
        path_study = self.path_to_studies / name

        self.study_service.assert_study_exist(name)

        if compact:
            config, study = self.study_factory.create_from_fs(
                path=self.path_to_studies / name
            )

            if not outputs:
                config.outputs = dict()
                study = self.study_factory.create_from_config(config)

            data = study.get()
            del study
            return self.exporter.export_compact(path_study, data)
        else:
            return self.exporter.export_file(path_study, outputs)
