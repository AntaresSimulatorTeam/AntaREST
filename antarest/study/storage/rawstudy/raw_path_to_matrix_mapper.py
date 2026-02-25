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
from typing import Callable

import polars as pl

from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_8_7


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

    def _get_matrix_inside_output_folder(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        # todo
        raise NotImplementedError("We do not handle output files for the moment")

    def _get_matrix_inside_input_folder(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        study_version = self._dao.get_version()

        if not parts:
            raise ValueError(error_msg)

        prefix, rest = parts[0], parts[1:]
        if prefix == "wind":
            if len(rest) != 2 and rest[0] != "series":
                raise ValueError(error_msg)
            return self._dao.get_wind(rest[1].removeprefix("wind_"))

        elif prefix == "solar":
            if len(rest) != 2 and rest[0] != "series":
                raise ValueError(error_msg)
            return self._dao.get_solar(rest[1].removeprefix("solar_"))

        elif prefix == "load":
            if len(rest) != 2 and rest[0] != "series":
                raise ValueError(error_msg)
            return self._dao.get_load(rest[1].removeprefix("load_"))

        elif prefix == "reserves":
            if len(rest) != 1:
                raise ValueError(error_msg)
            return self._dao.get_reserves(rest[0])

        elif prefix == "misc-gen":
            if len(rest) != 1:
                raise ValueError(error_msg)
            return self._dao.get_misc_gen(rest[0].removeprefix("miscgen-"))

        elif prefix == "bindingconstraints":
            if len(rest) != 1:
                raise ValueError(error_msg)
            if study_version < STUDY_VERSION_8_7:
                return self._dao.get_constraint_values_matrix(rest[0])
            # Based on the suffix we'll know which DAO method to use
            mapping: dict[str, Callable[[str], pl.DataFrame]] = {
                "lt": self._dao.get_constraint_less_term_matrix,
                "gt": self._dao.get_constraint_greater_term_matrix,
                "eq": self._dao.get_constraint_equal_term_matrix,
            }
            bc_id, suffix = rest[0][:-3], rest[0][-2:]
            return mapping[suffix](bc_id)

        """
        children: TREE = {
            "areas": InputAreas(self.matrix_mapper, config.next_file("areas")),
            "hydro": InputHydro(self.matrix_mapper, config.next_file("hydro")),
            "links": InputLink(self.matrix_mapper, config.next_file("links")),
            "thermal": InputThermal(self.matrix_mapper, config.next_file("thermal")),
        }
            children["renewables"] = ClusteredRenewables(self.matrix_mapper, config.next_file("renewables"))
            children["st-storage"] = InputSTStorage(self.matrix_mapper, config.next_file("st-storage"))
        pass
        """
