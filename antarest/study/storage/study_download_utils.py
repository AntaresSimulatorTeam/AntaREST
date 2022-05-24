import csv
import json
import logging
import os
import re
import tarfile
from datetime import datetime, timedelta
from http import HTTPStatus
from io import BytesIO, StringIO
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)
from zipfile import ZipFile, ZIP_DEFLATED

from fastapi import HTTPException

from antarest.study.model import (
    MatrixAggregationResult,
    StudyDownloadDTO,
    StudyDownloadLevelDTO,
    StudyDownloadType,
    ExportFormat,
    MatrixAggregationResultDTO,
    TimeSerie,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
    ENR_MODELLING,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
    FilterError,
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
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
        target: Tuple[StudyDownloadType, str],
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
                if len(column) > 0:
                    column_name = column[0]
                    if (
                        data.columns
                        and len(data.columns) > 0
                        and not (column_name in data.columns)
                    ):
                        continue

                    if target not in matrix.data:
                        matrix.data[target] = dict()

                    year_str = str(year)
                    if year_str not in matrix.data[target]:
                        matrix.data[target][year_str] = []

                    matrix.data[target][year_str].append(
                        TimeSerie(
                            name=column_name,
                            unit=column[1] if len(column) > 1 else "",
                            data=[row[index] for row in rows],
                        )
                    )
                else:
                    logger.warning(
                        f"Found an output column with no elements at {url}"
                    )

        except (ChildNotFoundError, FilterError) as e:
            matrix.warnings.append(f"{target} has no child")
            logger.warning(
                f"Failed to retrieve matrix data for {target}", exc_info=e
            )

    @staticmethod
    def level_output_filter(
        matrix: MatrixAggregationResult,
        year: int,
        target: Tuple[StudyDownloadType, str],
        study: FileStudyTree,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:

        cluster_details = [f"details-{data.level.value}"]
        if study.config.enr_modelling == ENR_MODELLING.CLUSTERS.value:
            cluster_details += [f"details-res-{data.level.value}"]

        files_matcher = (
            [f"values-{data.level.value}"] + cluster_details
            if data.includeClusters and target[0] != StudyDownloadType.LINK
            else [f"values-{data.level.value}"]
        )
        for elm in files_matcher:
            tmp_url = f"{url}/{elm}"
            StudyDownloader.read_columns(
                matrix, year, target, study, tmp_url, data
            )

    @staticmethod
    def apply_type_filters(
        matrix: MatrixAggregationResult,
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
                                (data.type, f"{elm}^{out_link}"),
                                study,
                                link_url,
                                data,
                            )
            else:
                StudyDownloader.level_output_filter(
                    matrix, year, (data.type, elm), study, url, data
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
        year: int,
        config: FileStudyTreeConfig,
        study: FileStudyTree,
        url: str,
        data: StudyDownloadDTO,
    ) -> None:
        if data.type == StudyDownloadType.AREA:
            StudyDownloader.select_filter(
                matrix, year, config.areas, study, f"{url}/areas", data
            )
        elif data.type == StudyDownloadType.DISTRICT:
            StudyDownloader.select_filter(
                matrix,
                year,
                {k: v for k, v in config.sets.items() if v.output},
                study,
                f"{url}/areas",
                data,
            )
        else:
            StudyDownloader.select_filter(
                matrix, year, config.areas, study, f"{url}/links", data
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
                    matrix, year, config, study, tmp_url, data
                )
        else:
            years = config.outputs[output_id].nbyears
            for year in range(1, years + 1):
                prefix = str(year).zfill(5)
                tmp_url = f"{url}/{prefix}"
                StudyDownloader.type_output_filter(
                    matrix, year, config, study, tmp_url, data
                )

    @staticmethod
    def build(
        file_study: FileStudy,
        output_id: str,
        data: StudyDownloadDTO,
    ) -> MatrixAggregationResultDTO:
        """
        Download outputs
        Args:
            file_study: file study object
            output_id: output id
            data: Json parameters
        Returns: JSON content file

        """
        # TODO: unarchive output
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
        return matrix.to_dto()

    @staticmethod
    def export_infos(
        data: Dict[str, List[TimeSerie]]
    ) -> Tuple[int, List[str]]:
        years = list(data.keys())
        if len(years) > 0:
            columns: List[str] = list(
                map(lambda x: f"{x.name}", data[years[0]])
            )
            if len(columns) > 0:
                return len(data[years[0]][0].data), (
                    ["Time", "Version"] + columns
                )
        return -1, []

    @staticmethod
    def export(
        matrix: MatrixAggregationResultDTO,
        filetype: ExportFormat,
        target_file: Path,
    ) -> None:
        if filetype == ExportFormat.JSON:
            # 1- JSON
            with open(target_file, "w") as fh:
                json.dump(
                    matrix.dict(),
                    fh,
                    ensure_ascii=False,
                    allow_nan=True,
                    indent=None,
                    separators=(",", ":"),
                )
        else:
            # 1- Zip/tar+gz container
            with (
                ZipFile(target_file, "w", ZIP_DEFLATED)  # type: ignore
                if filetype == ExportFormat.ZIP
                else tarfile.open(target_file, mode="w:gz")
            ) as output_data:

                # 2 - Create CSV files
                for ts_data in matrix.data:
                    output = StringIO()
                    writer = csv.writer(output, quoting=csv.QUOTE_NONE)
                    nb_rows, csv_titles = StudyDownloader.export_infos(
                        ts_data.data
                    )
                    if nb_rows == -1:
                        raise Exception(
                            f"Outputs export:  No rows for  {ts_data.name} csv"
                        )
                    writer.writerow(csv_titles)
                    row_date = datetime.strptime(
                        matrix.index.start_date, "%Y-%m-%d %H:%M:%S"
                    )
                    for year in ts_data.data:
                        for i in range(0, nb_rows):
                            columns = ts_data.data[year]
                            csv_row: List[Optional[Union[int, float, str]]] = [
                                str(row_date),
                                int(year),
                            ]
                            csv_row.extend(
                                [
                                    column_data.data[i]
                                    for column_data in columns
                                ]
                            )
                            writer.writerow(csv_row)
                            if (
                                matrix.index.level
                                == StudyDownloadLevelDTO.WEEKLY
                                and i == 0
                            ):
                                row_date = row_date + timedelta(
                                    days=matrix.index.first_week_size
                                )
                            else:
                                row_date = matrix.index.level.inc_date(
                                    row_date
                                )

                    bytes_data = str.encode(output.getvalue(), "utf-8")
                    if isinstance(output_data, ZipFile):
                        output_data.writestr(f"{ts_data.name}.csv", bytes_data)
                    else:
                        data_file = BytesIO(bytes_data)
                        data_file.seek(0, os.SEEK_END)
                        file_size = data_file.tell()
                        data_file.seek(0)
                        info = tarfile.TarInfo(name=f"{ts_data.name}.csv")
                        info.size = file_size
                        output_data.addfile(tarinfo=info, fileobj=data_file)


class BadOutputFormat(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.EXPECTATION_FAILED, message)


def find_first_child(
    folder_node: INode[Any, Any, Any], filter_name: str = ".*"
) -> INode[Any, Any, Any]:
    children: Dict[str, INode[Any, Any, Any]] = cast(
        FolderNode, folder_node
    ).build()
    try:
        first_child = filter(
            lambda el: re.search(filter_name, el) is not None,
            children.keys(),
        ).__next__()
    except StopIteration:
        raise BadOutputFormat("Couldn't find an output sample")
    return children[first_child]


def get_output_variables_information(
    study: FileStudy, output_name: str
) -> Dict[str, List[str]]:
    if not study.config.outputs[output_name].by_year:
        raise BadOutputFormat("Not a year by year simulation")

    # TODO: unzip if archived

    first_year_result: Dict[str, INode[Any, Any, Any]] = cast(
        FolderNode,
        find_first_child(
            cast(
                FolderNode,
                study.tree.get_node(
                    [
                        "output",
                        output_name,
                        study.config.outputs[output_name].mode,
                        "mc-ind",
                    ]
                ),
            ),
        ),
    ).build()

    output_variables = {
        "area": (
            cast(
                OutputSeriesMatrix,
                find_first_child(
                    find_first_child(first_year_result["areas"]), "values-"
                ),
            )
            .parse_dataframe()
            .columns.to_list()
        ),
        "link": [],
    }

    first_area_with_link: Optional[str] = None
    for area_id, area in study.config.areas.items():
        if area.links.keys():
            first_area_with_link = area_id
            break
    if first_area_with_link:
        output_variables["link"] = (
            cast(
                OutputSeriesMatrix,
                find_first_child(
                    find_first_child(
                        find_first_child(
                            first_year_result["links"],
                            f"^{first_area_with_link}$",
                        ),
                    ),
                    "values-",
                ),
            )
            .parse_dataframe()
            .columns.to_list()
        )

    return {
        "area": [col[0] for col in output_variables["area"]],
        "link": [col[0] for col in output_variables["link"]],
    }
