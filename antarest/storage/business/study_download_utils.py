import re
from typing import Callable, Tuple, Any
from antarest.storage.business.raw_study_service import RawStudyService
from antarest.storage.model import (
    MatrixAggregationResult,
    RawStudy,
    StudyDownloadDTO,
    MatrixColumn,
    StudyDownloadLevelDTO,
    StudyDownloadType,
)
from antarest.storage.repository.filesystem.folder_node import (
    ChildNotFoundError,
    FilterError,
)
from antarest.storage.repository.filesystem.root.study import Study
from antarest.storage.repository.filesystem.config.model import StudyConfig


class StudyDownloader:
    """Service to manage studies download"""

    @staticmethod
    def read_columns(
        matrix: MatrixAggregationResult,
        prefix: str,
        study: Study,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:
        parts = [item for item in url.split("/") if item]
        try:
            elm = study.get(parts)
            columns = elm["columns"]
            rows = elm["data"]
            filter_column = data.columns and len(data.columns) > 0

            for index, column in enumerate(columns):
                column_name = (
                    prefix + "|" + "|".join([c for c in column if c.strip()])
                )
                if filter_column:
                    if not (column_name in data.columns):
                        continue
                matrix[column_name] = MatrixColumn(
                    data=[row[index] for row in rows]
                )
        except (ChildNotFoundError, FilterError):
            pass

    @staticmethod
    def level_output_filter(
        matrix: MatrixAggregationResult,
        prefix: str,
        study: Study,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:

        if StudyDownloadLevelDTO.from_dict(data.level):
            files_matcher = (
                [f"values-{str(data.level)}", f"details-{str(data.level)}"]
                if data.includeClusters
                else [f"values-{str(data.level)}"]
            )
            for elm in files_matcher:
                tmp_url = f"{url}/{elm}"
                StudyDownloader.read_columns(
                    matrix, prefix, study, tmp_url, data
                )

    @staticmethod
    def apply_filter_2(
        matrix: MatrixAggregationResult,
        prefix: str,
        type_elm: Any,
        elm: str,
        study: Study,
        url: str,
        data: StudyDownloadDTO,
        filter_1: bool,
        filter_2: Callable[[str], bool],
    ) -> None:

        if filter_1:
            if StudyDownloadType.from_dict(
                data.type
            ) == StudyDownloadType.LINK and isinstance(type_elm[elm], list):
                for out_link in type_elm[elm]:
                    if filter_2(out_link):
                        tmp_prefix = f"{prefix}|{elm}^{out_link}"
                        link_url = f"{url}/{out_link}"
                        StudyDownloader.level_output_filter(
                            matrix, tmp_prefix, study, link_url, data
                        )
            else:
                tmp_prefix = f"{prefix}|{elm}"
                StudyDownloader.level_output_filter(
                    matrix, tmp_prefix, study, url, data
                )

    @staticmethod
    def get_filters(filter: str) -> Tuple[str, str]:
        if filter and len(filter) > 0:
            tmp_filters = filter.split(">")
            if len(tmp_filters) >= 2:
                return tmp_filters[0], tmp_filters[1]
            else:
                return filter, ""
        return "", ""

    @staticmethod
    def apply_filter_1(
        matrix: MatrixAggregationResult,
        prefix: str,
        type_elm: Any,
        study: Study,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:
        for elm in type_elm.keys():
            filtered_url = (
                f"{url}/@ {elm}"
                if StudyDownloadType.from_dict(data.type)
                == StudyDownloadType.CLUSTER
                else f"{url}/{elm}"
            )

            # Filter has priority over FilterIn or FilterOut
            if data.filter and len(data.filter) > 0:
                for flt in data.filter:
                    tmp_filters = flt.split(">")
                    if len(tmp_filters) >= 2:
                        flt_1, flt_2 = tuple(tmp_filters[:2])
                        StudyDownloader.apply_filter_2(
                            matrix,
                            prefix,
                            type_elm,
                            elm,
                            study,
                            filtered_url,
                            data,
                            flt_1 == elm,
                            lambda x: not (flt_2 and x != flt_2),
                        )
                    else:
                        StudyDownloader.apply_filter_2(
                            matrix,
                            prefix,
                            type_elm,
                            elm,
                            study,
                            filtered_url,
                            data,
                            flt == elm,
                            lambda x: True,
                        )
            else:  # FilterIn, FilterOut
                flt_out_1, flt_out_2 = (
                    StudyDownloader.get_filters(data.filterOut)
                    if data.filterOut
                    else ("", "")
                )
                flt_in_1, flt_in_2 = (
                    StudyDownloader.get_filters(data.filterIn)
                    if data.filterIn
                    else ("", "")
                )

                filter_1_in = bool(re.search(flt_in_1, elm))
                filter_1_out = (
                    not bool(re.search(flt_out_1, elm)) if flt_out_1 else True
                )
                filter_1 = filter_1_in and filter_1_out

                def filter_2(x: str) -> bool:
                    cond1 = not (flt_out_2 and bool(re.search(flt_out_2, x)))
                    cond2 = not (flt_in_2 and not bool(re.search(flt_in_2, x)))
                    return cond1 and cond2

                StudyDownloader.apply_filter_2(
                    matrix,
                    prefix,
                    type_elm,
                    elm,
                    study,
                    filtered_url,
                    data,
                    filter_1,
                    filter_2,
                )

    @staticmethod
    def type_output_filter(
        matrix: MatrixAggregationResult,
        prefix: str,
        config: StudyConfig,
        study: Study,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:
        if StudyDownloadType.from_dict(data.type) == StudyDownloadType.AREA:
            StudyDownloader.apply_filter_1(
                matrix, prefix, config.areas, study, f"{url}/areas", data
            )
        elif (
            StudyDownloadType.from_dict(data.type) == StudyDownloadType.CLUSTER
        ):
            StudyDownloader.apply_filter_1(
                matrix, prefix, config.sets, study, f"{url}/areas", data
            )
        else:
            StudyDownloader.apply_filter_1(
                matrix, prefix, config.links, study, f"{url}/links", data
            )

    @staticmethod
    def years_output_filter(
        matrix: MatrixAggregationResult,
        config: StudyConfig,
        output_id: str,
        study: Study,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:
        if data.years and len(data.years) > 0:
            for year in data.years:
                prefix = str(year).zfill(5)
                tmp_url = f"{url}/{prefix}"
                StudyDownloader.type_output_filter(
                    matrix, prefix, config, study, tmp_url, data
                )
        else:
            years = config.outputs[output_id].nbyears
            for year in range(1, years + 1):
                prefix = str(year).zfill(5)
                tmp_url = f"{url}/{prefix}"
                StudyDownloader.type_output_filter(
                    matrix, prefix, config, study, tmp_url, data
                )

    @staticmethod
    def build(
        study_service: RawStudyService,
        study: RawStudy,
        output_id: str,
        url: str,
        data: StudyDownloadDTO,
    ) -> MatrixAggregationResult:
        """
        Download outputs
        Args:
            study_service: service to manage services
            study: study we want to parse
            output_id: output id
            url: link to /economy directory
            data: Json parameters
        Returns: JSON content file

        """
        tmp_url = url
        matrix: MatrixAggregationResult = dict()
        study_path = study_service.get_study_path(study)
        config, study_root = study_service.study_factory.create_from_fs(
            study_path
        )
        if data.synthesis:
            tmp_url += "/mc-all"
            StudyDownloader.type_output_filter(
                matrix, "", config, study_root, tmp_url, data
            )
        else:
            tmp_url += "/mc-ind"
            StudyDownloader.years_output_filter(
                matrix, config, output_id, study_root, tmp_url, data
            )
        return matrix
