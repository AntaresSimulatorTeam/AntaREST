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
import io
import logging
import shutil
from pathlib import Path
from typing import Optional

import numpy as np
import polars as pl
from polars.exceptions import NoDataError
from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.serde.matrix_export import write_dataframe_in_tsv_format
from antarest.core.serde.np_array import NpArray
from antarest.core.utils.archives import read_original_file_in_archive
from antarest.core.utils.polars import create_polars_dataframe, read_input_dataframe
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.model import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode, dump_dataframe

logger = logging.getLogger(__name__)


class InputSeriesMatrix(MatrixNode):
    """
    Generic node to handle input matrix behavior
    """

    def __init__(
        self,
        matrix_mapper: MatrixUriMapper,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency = MatrixFrequency.HOURLY,
        nb_columns: Optional[int] = None,
        default_empty: Optional[NpArray] = None,  # optional only for the capacity matrix in Xpansion
        should_exist: bool = True,
    ):
        super().__init__(matrix_mapper=matrix_mapper, config=config, freq=freq)
        self.nb_columns = nb_columns
        if default_empty is None:
            self.default_empty = None
        else:
            # Clone the template value and make it writable
            self.default_empty = np.copy(default_empty)
            self.default_empty.flags.writeable = True
        # Removes the .link suffix if the matrix is normalized
        self.config.path = self.config.path.parent / self.config.path.name.removesuffix(".link")
        self.should_exist = should_exist

    @override
    def parse_as_dataframe(self, file_path: Optional[Path] = None) -> pl.DataFrame:
        file_path = file_path or self.config.path
        try:
            stopwatch = StopWatch()
            link_content = self.matrix_mapper.get_link_content(self)
            if link_content:
                matrix = self.matrix_mapper.get_matrix(link_content)
            else:
                try:
                    matrix = read_input_dataframe(file_path, has_headers=False)
                except FileNotFoundError as e:
                    # Some matrices are optional and not required by the Simulator
                    # If so, we shouldn't raise but just return the `default_empty` value
                    if not self.should_exist:
                        if self.default_empty is not None:
                            return create_polars_dataframe(self.default_empty)
                        return pl.DataFrame()
                    # Otherwise, we raise a 404 'Not Found' exception.
                    logger.warning(f"Matrix file'{file_path}' not found")
                    study_id = self.config.study_id
                    relpath = file_path.relative_to(self.config.study_path).as_posix()
                    raise ChildNotFoundError(f"File '{relpath}' not found in the study '{study_id}'") from e

                matrix.columns = [str(i) for i in range(len(matrix.columns))]

            stopwatch.log_elapsed(lambda x: logger.debug(f"Matrix parsed in {x}s"))
            if matrix.is_empty():
                raise NoDataError
            return matrix
        except NoDataError:
            logger.warning(f"Empty file found when parsing {file_path}")
            final_matrix = pl.DataFrame()
            if self.default_empty is not None:
                final_matrix = create_polars_dataframe(self.default_empty)
            return final_matrix

    @override
    def write_dataframe(self, df: pl.DataFrame) -> None:
        # If the DataFrame content corresponds to the `default_empty` attribute, we should just create an empty file.
        # This way, we can write the content quicker, and the file takes less place on the fs.
        if df.is_empty() or self.default_empty is not None and np.array_equal(df.to_numpy(), self.default_empty):
            self.config.path.write_text("")
        else:
            write_dataframe_in_tsv_format(df, self.config.path)
        self.matrix_mapper.remove_link(self)

    def _infer_path(self) -> Path:
        link_path = self.matrix_mapper.get_link_path(self)
        if link_path.exists():
            return link_path
        elif self.config.path.exists():
            return self.config.path
        raise ChildNotFoundError(f"Neither link file {link_path} nor matrix file {self.config.path} exists")

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
        elif self.matrix_mapper.has_link(self):
            target_path = self.config.path.with_suffix(".txt")
            buffer = io.BytesIO()
            df = self.parse_as_dataframe()
            dump_dataframe(df, buffer)
            content = buffer.getvalue()
            suffix = target_path.suffix
            filename = target_path.name
        else:
            content = self.config.path.read_bytes()

        if content == b"" and self.default_empty is not None:
            # The file is empty, we should return the `default_empty` value
            buffer = io.BytesIO()
            dump_dataframe(pl.DataFrame(self.default_empty), buffer)
            content = buffer.getvalue()

        return OriginalFile(content=content, suffix=suffix, filename=filename)
