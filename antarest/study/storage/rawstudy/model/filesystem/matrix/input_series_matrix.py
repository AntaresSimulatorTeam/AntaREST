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
import io
import logging
import shutil
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from numpy import typing as npt
from pandas.errors import EmptyDataError
from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.model import JSON
from antarest.core.utils.archives import read_original_file_in_archive
from antarest.core.utils.utils import StopWatch
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency, MatrixNode, dump_dataframe

logger = logging.getLogger(__name__)


class InputSeriesMatrix(MatrixNode):
    """
    Generic node to handle input matrix behavior
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency = MatrixFrequency.HOURLY,
        nb_columns: Optional[int] = None,
        default_empty: Optional[npt.NDArray[np.float64]] = None,  # optional only for the capacity matrix in Xpansion
    ):
        super().__init__(context=context, config=config, freq=freq)
        self.nb_columns = nb_columns
        if default_empty is None:
            self.default_empty = None
        else:
            # Clone the template value and make it writable
            self.default_empty = np.copy(default_empty)
            self.default_empty.flags.writeable = True
        # Removes the .link suffix if the matrix is normalized
        self.config.path = self.config.path.parent / self.config.path.name.removesuffix(".link")

    @override
    def parse_as_dataframe(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        file_path = file_path or self.config.path
        try:
            stopwatch = StopWatch()
            link_path = self.get_link_path()
            if link_path.exists():
                link = link_path.read_text()
                matrix = self.context.resolver.get_matrix(link)
            else:
                try:
                    matrix = pd.read_csv(
                        file_path,
                        sep="\t",
                        dtype=float,
                        header=None,
                        float_precision="legacy",
                    )
                except FileNotFoundError as e:
                    # Raise 404 'Not Found' if the TSV file is not found
                    logger.warning(f"Matrix file'{file_path}' not found")
                    study_id = self.config.study_id
                    relpath = file_path.relative_to(self.config.study_path).as_posix()
                    raise ChildNotFoundError(f"File '{relpath}' not found in the study '{study_id}'") from e
            stopwatch.log_elapsed(lambda x: logger.info(f"Matrix parsed in {x}s"))
            final_matrix = matrix.dropna(how="any", axis=1)
            if final_matrix.empty:
                raise EmptyDataError
            return final_matrix
        except EmptyDataError:
            logger.warning(f"Empty file found when parsing {file_path}")
            final_matrix = pd.DataFrame()
            if self.default_empty is not None:
                final_matrix = pd.DataFrame(self.default_empty)
            return final_matrix

    @override
    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        self._assert_url_end(url)

        errors = []
        if not self.config.path.exists():
            errors.append(f"Input Series Matrix f{self.config.path} not exists")
        if self.nb_columns and len(data) != self.nb_columns:
            errors.append(f"{self.config.path}: Data was wrong size. expected {self.nb_columns} get {len(data)}")
        return errors

    def _infer_path(self) -> Path:
        if self.get_link_path().exists():
            return self.get_link_path()
        elif self.config.path.exists():
            return self.config.path
        raise ChildNotFoundError(f"Neither link file {self.get_link_path()} nor matrix file {self.config.path} exists")

    def rename_file(self, target: str) -> None:
        target_path = self.config.path.parent.joinpath(f"{target}{''.join(self._infer_path().suffixes)}")
        target_path.unlink(missing_ok=True)
        self._infer_path().rename(target_path)

    def copy_file(self, target: str) -> None:
        target_path = self.config.path.parent.joinpath(f"{target}{''.join(self._infer_path().suffixes)}")
        target_path.unlink(missing_ok=True)
        shutil.copy(self._infer_path(), target_path)

    @override
    def get_file_content(self) -> OriginalFile:
        suffix = self.config.path.suffix
        filename = self.config.path.name
        if self.config.archive_path:
            content = read_original_file_in_archive(
                self.config.archive_path, self.get_relative_path_inside_archive(self.config.archive_path)
            )
        elif self.get_link_path().is_file():
            target_path = self.config.path.with_suffix(".txt")
            buffer = io.BytesIO()
            df = self.parse_as_dataframe()
            dump_dataframe(df, buffer, None)
            content = buffer.getvalue()
            suffix = target_path.suffix
            filename = target_path.name
        else:
            content = self.config.path.read_bytes()
        return OriginalFile(content=content, suffix=suffix, filename=filename)
