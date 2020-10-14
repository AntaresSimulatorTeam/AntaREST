from pathlib import Path
from typing import Any

from api_iso_antares.antares_io.reader import FolderReaderEngine
from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.engine import UrlEngine


class StudyNotFoundError(HtmlException):
    def __init__(self, message: str):
        super(StudyNotFoundError, self).__init__(message, 404)


class RequestHandlerParameters:
    def __init__(self, depth: int = 3) -> None:
        self.depth = depth

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, type(self)) and self.__dict__ == other.__dict__
        )

    def __str__(self) -> str:
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                [
                    "{}={} ({})".format(
                        k, str(self.__dict__[k]), type(self.__dict__[k])
                    )
                    for k in sorted(self.__dict__)
                ]
            ),
        )

    def __repr__(self) -> str:
        return self.__str__()


class RequestHandler:
    def __init__(
        self,
        study_reader: FolderReaderEngine,
        url_engine: UrlEngine,
        path_to_studies: Path,
    ):
        self.study_reader = study_reader
        self.url_engine = url_engine
        self.path_to_studies = path_to_studies

    def get(self, route: str, parameters: RequestHandlerParameters) -> Any:
        path_route = Path(route)
        study_name = path_route.parts[0]
        self._assert_study_exist(study_name)

        data = self.study_reader.read(self.path_to_studies / study_name)
        self.study_reader.validate(data)

        route_cut = path_route.relative_to(Path(study_name))
        return self.url_engine.apply(route_cut, data, parameters.depth)

    def _assert_study_exist(self, study_name: str) -> None:
        dirs_files = self.path_to_studies.glob(pattern="*")
        dirs = [str(folder.name) for folder in dirs_files if folder.is_dir()]
        if study_name not in dirs:
            raise StudyNotFoundError(f"{study_name} not found")
