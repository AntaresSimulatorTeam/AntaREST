# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
from polars.exceptions import InvalidOperationError, NoDataError
from typing_extensions import override

from antarest.study.business.model.gems.calendar import GemsCalendar, get_calendar_datetime_format
from antarest.study.dao.api.gems_calendar_dao import GemsCalendarDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


def _get_gems_calendar_file_path(study_path: Path) -> Path:
    return study_path / "input" / "calendar_file.csv"


def read_gems_calendar(file_path: Path) -> GemsCalendar:
    error_msg = "Calendar file must have these exact columns 'absolute_time_index', 'block', and 'granular_date'"

    try:
        df = pl.read_csv(file_path)
    except NoDataError:
        raise ValueError(error_msg)

    if df.columns != ["absolute_time_index", "block", "granular_date"]:
        raise ValueError(error_msg)

    date_time_format = get_calendar_datetime_format()
    try:
        df = df.with_columns(pl.col("granular_date").str.to_datetime(date_time_format).alias("granular_date"))
    except InvalidOperationError:
        raise ValueError(f"Calendar file column 'granular_date' must follow this format: {date_time_format}")

    return GemsCalendar.model_validate({"data": df.to_dicts()})


class FileStudyGemsCalendarDao(GemsCalendarDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_gems_calendar(self) -> GemsCalendar | None:
        path = _get_gems_calendar_file_path(self.get_file_study().config.study_path)
        if not path.exists():
            return None

        return read_gems_calendar(path)

    @override
    def save_gems_calendar(self, calendar: GemsCalendar) -> None:
        path = _get_gems_calendar_file_path(self.get_file_study().config.study_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        df = pl.DataFrame(calendar.data)
        # Write datetime column as string
        df = df.with_columns(pl.col("granular_date").dt.strftime(get_calendar_datetime_format()))
        df.write_csv(path, separator=",", include_header=True)
