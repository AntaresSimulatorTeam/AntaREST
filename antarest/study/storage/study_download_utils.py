import calendar
import csv
import logging
import os
import re
import tarfile
import time
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from math import ceil
from pathlib import Path
from time import strptime
from typing import Any, Callable, Dict, List, Optional, Tuple, cast
from zipfile import ZipFile, ZIP_DEFLATED

from antarest.study.model import (
    MatrixAggregationResult,
    StudyDownloadDTO,
    StudyDownloadLevelDTO,
    StudyDownloadType,
    MatrixIndex,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
    FilterError,
)
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.utils import get_start_date

logger = logging.getLogger(__name__)


class StudyDownloader:
    """Service to manage studies download"""

    @staticmethod
    def read_columns(
        matrix: MatrixAggregationResult,
        year: int,
        area_name: str,
        study: FileStudyTree,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:
        parts = [item for item in url.split("/") if item]
        try:
            elm = study.get(parts)
            columns = elm["columns"]
            rows = elm["data"]

            for index, column in enumerate(columns):
                column_name = "|".join([c for c in column if c.strip()])
                if (
                    data.columns
                    and len(data.columns) > 0
                    and not (column_name in data.columns)
                ):
                    continue

                if area_name not in matrix.data:
                    matrix.data[area_name] = dict()

                year_str = str(year)
                if year_str not in matrix.data[area_name]:
                    matrix.data[area_name][year_str] = dict()

                matrix.data[area_name][year_str][column_name] = [
                    row[index] for row in rows
                ]

        except (ChildNotFoundError, FilterError) as e:
            matrix.warnings.append(f"{area_name} has no child")
            logger.warning(
                f"Failed to retrieve matrix data for {area_name}", exc_info=e
            )

    @staticmethod
    def level_output_filter(
        matrix: MatrixAggregationResult,
        year: int,
        area_name: str,
        study: FileStudyTree,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:

        files_matcher = (
            [f"values-{data.level.value}", f"details-{data.level.value}"]
            if data.includeClusters
            else [f"values-{data.level.value}"]
        )
        for elm in files_matcher:
            tmp_url = f"{url}/{elm}"
            StudyDownloader.read_columns(
                matrix, year, area_name, study, tmp_url, data
            )

    @staticmethod
    def apply_type_filters(
        matrix: MatrixAggregationResult,
        prefix: str,
        year: int,
        type_elm: Any,
        elm: str,
        study: FileStudyTree,
        url: str,
        data: StudyDownloadDTO,
        first_element_type_condition: bool,
        second_element_type_condition: Callable[[str], bool],
    ) -> None:

        if first_element_type_condition:
            if data.type == StudyDownloadType.LINK and isinstance(
                type_elm[elm], Area
            ):
                if type_elm[elm].links:
                    for out_link in type_elm[elm].links.keys():
                        if second_element_type_condition(out_link):
                            link_url = f"{url}/{out_link}"
                            StudyDownloader.level_output_filter(
                                matrix,
                                year,
                                f"{elm}^{out_link}",
                                study,
                                link_url,
                                data,
                            )
            else:
                StudyDownloader.level_output_filter(
                    matrix, year, elm, study, url, data
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
    def select_filter(
        matrix: MatrixAggregationResult,
        prefix: str,
        year: int,
        type_elm: Any,
        study: FileStudyTree,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:
        for elm in type_elm.keys():
            filtered_url = (
                f"{url}/@ {elm}"
                if data.type == StudyDownloadType.DISTRICT
                else f"{url}/{elm}"
            )

            # Filter has priority over FilterIn or FilterOut
            if data.filter and len(data.filter) > 0:
                for flt in data.filter:
                    #  ">" is a separator character used only for links
                    tmp_filters = flt.split(">")
                    if len(tmp_filters) >= 2:
                        flt_1, flt_2 = tuple(tmp_filters[:2])
                        StudyDownloader.apply_type_filters(
                            matrix,
                            prefix,
                            year,
                            type_elm,
                            elm,
                            study,
                            filtered_url,
                            data,
                            flt_1 == elm,
                            lambda x: not (flt_2 and x != flt_2),
                        )
                    else:
                        StudyDownloader.apply_type_filters(
                            matrix,
                            prefix,
                            year,
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

                first_element_type_condition_in = bool(
                    re.search(flt_in_1, elm)
                )
                first_element_type_condition_out = (
                    not bool(re.search(flt_out_1, elm)) if flt_out_1 else True
                )
                first_element_type_condition = (
                    first_element_type_condition_in
                    and first_element_type_condition_out
                )

                def second_element_type_condition(x: str) -> bool:
                    cond1 = not (flt_out_2 and bool(re.search(flt_out_2, x)))
                    cond2 = not (flt_in_2 and not bool(re.search(flt_in_2, x)))
                    return cond1 and cond2

                StudyDownloader.apply_type_filters(
                    matrix,
                    prefix,
                    year,
                    type_elm,
                    elm,
                    study,
                    filtered_url,
                    data,
                    first_element_type_condition,
                    second_element_type_condition,
                )

    @staticmethod
    def type_output_filter(
        matrix: MatrixAggregationResult,
        prefix: str,
        year: int,
        config: FileStudyTreeConfig,
        study: FileStudyTree,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:
        if data.type == StudyDownloadType.AREA:
            StudyDownloader.select_filter(
                matrix, prefix, year, config.areas, study, f"{url}/areas", data
            )
        elif data.type == StudyDownloadType.DISTRICT:
            StudyDownloader.select_filter(
                matrix,
                prefix,
                year,
                {k: v for k, v in config.sets.items() if v.output},
                study,
                f"{url}/areas",
                data,
            )
        else:
            StudyDownloader.select_filter(
                matrix, prefix, year, config.areas, study, f"{url}/links", data
            )

    @staticmethod
    def years_output_filter(
        matrix: MatrixAggregationResult,
        config: FileStudyTreeConfig,
        output_id: str,
        study: FileStudyTree,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:
        if data.years and len(data.years) > 0:
            for year in data.years:
                prefix = str(year).zfill(5)
                tmp_url = f"{url}/{prefix}"
                StudyDownloader.type_output_filter(
                    matrix, prefix, year, config, study, tmp_url, data
                )
        else:
            years = config.outputs[output_id].nbyears
            for year in range(1, years + 1):
                prefix = str(year).zfill(5)
                tmp_url = f"{url}/{prefix}"
                StudyDownloader.type_output_filter(
                    matrix, prefix, year, config, study, tmp_url, data
                )

    @staticmethod
    def build(
        file_study: FileStudy,
        output_id: str,
        data: StudyDownloadDTO,
    ) -> MatrixAggregationResult:
        """
        Download outputs
        Args:
            file_study: file study object
            output_id: output id
            data: Json parameters
        Returns: JSON content file

        """
        url = f"/output/{output_id}"
        matrix: MatrixAggregationResult = MatrixAggregationResult(
            index=get_start_date(file_study, output_id, data.level),
            data=dict(),
            warnings=[],
        )

        if (
            file_study.config.outputs
            and output_id in file_study.config.outputs
        ):
            sim = file_study.config.outputs[output_id]
            if sim:
                url += (
                    f"/{sim.mode}"
                    if sim.mode != "draft"
                    else f"/adequacy-draft"
                )

                if data.synthesis:
                    url += "/mc-all"
                    StudyDownloader.type_output_filter(
                        matrix,
                        "",
                        0,
                        file_study.config,
                        file_study.tree,
                        url,
                        data,
                    )
                else:
                    url += "/mc-ind"
                    StudyDownloader.years_output_filter(
                        matrix,
                        file_study.config,
                        output_id,
                        file_study.tree,
                        url,
                        data,
                    )
        return matrix

    @staticmethod
    def export_infos(
        data: Dict[str, Dict[str, List[Optional[float]]]]
    ) -> Tuple[int, List[str]]:
        years = list(data.keys())
        if len(years) > 0:
            columns: List[str] = list(data[years[0]].keys())
            if len(columns) > 0:
                return len(data[years[0]][columns[0]]), (
                    ["Time", "Version"] + columns
                )
        return -1, []

    @staticmethod
    def export(
        matrix: MatrixAggregationResult, type: str, target_file: Path
    ) -> None:

        # 1- Zip/tar+gz container
        with (
            ZipFile(target_file, "w", ZIP_DEFLATED)  # type: ignore
            if type == "application/zip"
            else tarfile.open(target_file, mode="w:gz")
        ) as output_data:

            # 2 - Create CSV files
            for area_name in matrix.data.keys():
                output = StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_NONE)
                nb_rows, csv_titles = StudyDownloader.export_infos(
                    matrix.data[area_name]
                )
                if nb_rows == -1:
                    raise Exception(
                        f"Outputs export:  No rows for  {area_name} csv"
                    )
                writer.writerow(csv_titles)
                row_date = datetime.strptime(
                    matrix.index.start_date, "%Y-%m-%d %H:%M:%S"
                )
                for year in matrix.data[area_name].keys():
                    for i in range(0, nb_rows):
                        columns = matrix.data[area_name][year]
                        csv_row: List[Optional[float]] = [
                            str(row_date),
                            float(year),
                        ]
                        csv_row.extend(
                            [columns[name][i] for name in columns.keys()]
                        )
                        writer.writerow(csv_row)
                        if (
                            matrix.index.level == StudyDownloadLevelDTO.WEEKLY
                            and i == 0
                        ):
                            row_date = row_date + timedelta(
                                days=matrix.index.first_week_size
                            )
                        else:
                            row_date = matrix.index.level.inc_date(row_date)

                bytes_data = str.encode(output.getvalue(), "utf-8")
                if isinstance(output_data, ZipFile):
                    output_data.writestr(f"{area_name}.csv", bytes_data)
                else:
                    data_file = BytesIO(bytes_data)
                    data_file.seek(0, os.SEEK_END)
                    file_size = data_file.tell()
                    data_file.seek(0)
                    info = tarfile.TarInfo(name=f"{area_name}.csv")
                    info.size = file_size
                    output_data.addfile(tarinfo=info, fileobj=data_file)
