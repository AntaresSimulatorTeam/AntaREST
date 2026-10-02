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
from __future__ import annotations

from dataclasses import dataclass

from antarest.matrixstore.service import ISimpleMatrixService


@dataclass(frozen=True)
class MatrixStorageContext:
    """
    Necessary context to decide how to read & write input timeseries to file study.

    Attributes:
        matrix_service: Service to store and retrieve matrices.
        is_managed: If True, write .link files pointing to the matrix service (managed study).
                    If False, write matrix data as plain TSV files on disk (unmanaged study).
    """

    matrix_service: ISimpleMatrixService
    is_managed: bool
