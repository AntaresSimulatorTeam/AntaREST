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
from pathlib import Path

import polars as pl

from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.dao.api.study_dao import StudyDao


class RawPathToMatrixMapper:
    """
    Parses a given path like `input/load/series/load_area_fr` to retrieve the corresponding matrix.
    Used for studies stored in database as the notion of path no longer exists for them.
    But to ensure backward compatibility for the `raw` endpoints we still have to return the matrices.
    """

    def __init__(self, dao: StudyDao) -> None:
        self._dao = dao

    def get_matrix_from_path(self, path: Path) -> pl.DataFrame:
        basic_error_msg = f"Path {path} does not point towards a matrix."

        parts = path.parts
        if not parts:
            raise ValueError(f"Path {path} is empty")

        prefix, rest = parts[0], parts[1:]

        if prefix == "output":
            return self._get_matrix_inside_output_folder(rest, basic_error_msg)

        if prefix == "user":
            return self._get_matrix_inside_user_dir(rest, basic_error_msg)

        if prefix == "input":
            return self._get_matrix_inside_input_folder(rest, basic_error_msg)

        raise ValueError(basic_error_msg)

    def _get_matrix_inside_user_dir(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        """The only possible matrices are expansion weights or capacities"""
        if len(parts) != 3 or parts[0] != "expansion" or parts[1] not in ["capa", "weights"]:
            raise ValueError(error_msg)

        if parts[1] == "capa":
            matrix = self._dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, parts[2])
        else:
            matrix = self._dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, parts[2])

        assert isinstance(matrix, pl.DataFrame)
        return matrix

    def _get_matrix_inside_input_folder(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        pass

    def _get_matrix_inside_output_folder(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        # todo
        raise NotImplementedError("We do not handle output files for the moment")
