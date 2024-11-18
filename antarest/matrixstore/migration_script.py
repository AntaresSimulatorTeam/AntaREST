# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

from antarest.core.config import InternalMatrixFormat

logger = logging.getLogger(__name__)


def migrate_matrix(matrix_path: Path, format: InternalMatrixFormat) -> None:
    new_path = matrix_path.parent.joinpath(matrix_path.stem + f".{format.value}")
    data = format.load_matrix(matrix_path)
    data = data.reshape((1, 0)) if data.size == 0 else data
    df = pd.DataFrame(data=data)
    format.save_matrix(df, new_path)
    old_lock_path = matrix_path.with_suffix(f"{matrix_path.suffix}.lock")
    if old_lock_path.exists():
        new_lock_path = new_path.with_suffix(f".{format.value}.lock")
        new_lock_path.touch()
        old_lock_path.rename(new_lock_path)
    matrix_path.unlink()


def migrate_matrixstore(matrix_store_path: Path, format: InternalMatrixFormat) -> None:
    """
    Migrates all matrices inside the matrixstore to a given format
    Does nothing if all files are already in the right format.
    """
    matrices = [f for f in matrix_store_path.glob("*") if f.suffixes[-1] != ".lock" and f.suffixes[0] != format.value]
    if matrices:
        logger.info("Matrix store migration starts")

        import multiprocessing
        from multiprocessing import Pool

        migrate_with_format = partial(migrate_matrix, format=format)
        with Pool(processes=multiprocessing.cpu_count()) as pool:
            pool.map(migrate_with_format, matrices)

        logger.info("Matrix store migration ended successfully")
