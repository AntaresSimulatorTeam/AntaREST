# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
import re
from pathlib import Path
from typing import Any, Callable, Tuple, cast

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.model import (
    STUDY_VERSION_8_1,
    MatrixAggregationResult,
    MatrixAggregationResultDTO,
    StudyDownloadDTO,
    StudyDownloadType,
    TimeSerie,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    AreaConfig,
    EnrModelling,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FilterError
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import OutputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.utils import get_start_date

logger = logging.getLogger(__name__)


class ExportException(Exception):
    """Exception raised during export when a matrix data is empty (no rows)."""


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
            elm = study.get_node(parts)
            df = cast(OutputSeriesMatrix, elm).parse_dataframe()
            columns = df.columns

            for index, column in enumerate(columns):
                if len(column) > 0:
                    column_name = column[0]
                    if data.columns and len(data.columns) > 0 and column_name not in data.columns:
                        continue

                    if target not in matrix.data:
                        matrix.data[target] = dict()

                    year_str = str(year)
                    if year_str not in matrix.data[target]:
                        matrix.data[target][year_str] = []

                    matrix.data[target][year_str].append(
                        TimeSerie.model_construct(
                            name=column_name,
                            unit=column[1] if len(column) > 1 else "",
                            data=df[column].to_numpy(),
                        )
                    )
                else:
                    logger.warning(f"Found an output column with no elements at {url}")

        except (ChildNotFoundError, FilterError) as e:
            matrix.warnings.append(f"{target} has no child")
            logger.warning(f"Failed to retrieve matrix data for {target}", exc_info=e)

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

        config = study.config
        has_renewables = (
            config.version >= STUDY_VERSION_8_1 and EnrModelling(config.enr_modelling) == EnrModelling.CLUSTERS
        )
        if has_renewables:
            cluster_details += [f"details-res-{data.level.value}"]

        files_matcher = (
            [f"values-{data.level.value}"] + cluster_details
            if data.includeClusters and target[0] != StudyDownloadType.LINK
            else [f"values-{data.level.value}"]
        )
        for elm in files_matcher:
            tmp_url = f"{url}/{elm}"
            StudyDownloader.read_columns(matrix, year, target, study, tmp_url, data)

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
            if data.type == StudyDownloadType.LINK and isinstance(type_elm[elm], AreaConfig):
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
                StudyDownloader.level_output_filter(matrix, year, (data.type, elm), study, url, data)

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
            filtered_url = f"{url}/@ {elm}" if data.type == StudyDownloadType.DISTRICT else f"{url}/{elm}"

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
                flt_out_1, flt_out_2 = StudyDownloader.get_filters(data.filterOut) if data.filterOut else ("", "")
                flt_in_1, flt_in_2 = StudyDownloader.get_filters(data.filterIn) if data.filterIn else ("", "")

                first_element_type_condition_in = bool(re.search(flt_in_1, elm))
                first_element_type_condition_out = not bool(re.search(flt_out_1, elm)) if flt_out_1 else True
                first_element_type_condition = first_element_type_condition_in and first_element_type_condition_out

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
            StudyDownloader.select_filter(matrix, year, config.areas, study, f"{url}/areas", data)
        elif data.type == StudyDownloadType.DISTRICT:
            StudyDownloader.select_filter(
                matrix,
                year,
                {k: v for k, v in config.districts.items() if v.output},
                study,
                f"{url}/areas",
                data,
            )
        else:
            StudyDownloader.select_filter(matrix, year, config.areas, study, f"{url}/links", data)

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
                StudyDownloader.type_output_filter(matrix, year, config, study, tmp_url, data)
        else:
            years = config.outputs[output_id].nbyears
            for year in range(1, years + 1):
                prefix = str(year).zfill(5)
                tmp_url = f"{url}/{prefix}"
                StudyDownloader.type_output_filter(matrix, year, config, study, tmp_url, data)

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
        url = f"/output/{output_id}"
        matrix: MatrixAggregationResult = MatrixAggregationResult(
            index=get_start_date(file_study, output_id, data.level),
            data={},
            warnings=[],
        )

        if file_study.config.outputs and output_id in file_study.config.outputs:
            sim = file_study.config.outputs[output_id]
            if sim:
                url += f"/{sim.mode.lower()}"

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
    def export(matrix: MatrixAggregationResultDTO, target_file: Path) -> None:
        with open(target_file, "w", encoding="utf-8") as fh:
            fh.write(matrix.model_dump_json())
