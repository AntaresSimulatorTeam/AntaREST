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

import glob
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def migrate_matrix(matrix_path_as_str: str) -> None:
    matrix_path = Path(matrix_path_as_str)
    hdf_path = matrix_path.parent.joinpath(matrix_path.stem + ".hdf")
    data = np.loadtxt(matrix_path, delimiter="\t", dtype=np.float64, ndmin=2)
    data = data.reshape((1, 0)) if data.size == 0 else data
    df = pd.DataFrame(data=data)
    df.to_hdf(str(hdf_path), "data")
    old_lock_path = matrix_path.with_suffix(".tsv.lock")
    new_lock_path = hdf_path.with_suffix(".hdf.lock")
    new_lock_path.touch()
    if old_lock_path.exists():
        old_lock_path.rename(new_lock_path)
    matrix_path.unlink()


def migrate_matrixstore(matrix_store_path: Path) -> None:
    """
    Migrates matrices inside the matrixstore from tsv files to hdf ones.
    Does nothing if all files are already hdf ones.
    """
    matrices = glob.glob(os.path.join(str(matrix_store_path), "*.tsv"))
    if matrices:
        logger.info("Matrix store migration starts")

        import multiprocessing
        from multiprocessing import Pool

        with Pool(processes=multiprocessing.cpu_count()) as pool:
            pool.map(migrate_matrix, matrices)

        logger.info("Matrix store migration ended successfully")
