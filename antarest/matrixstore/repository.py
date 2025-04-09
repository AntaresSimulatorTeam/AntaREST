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

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from filelock import FileLock
from sqlalchemy import exists  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from antarest.core.config import InternalMatrixFormat
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.model import Matrix, MatrixDataSet
from antarest.matrixstore.parsing import load_matrix, save_matrix

logger = logging.getLogger(__name__)


class MatrixDataSetRepository:
    """
    Database connector to manage Matrix metadata entity
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def save(self, matrix_user_metadata: MatrixDataSet) -> MatrixDataSet:
        res: bool = self.session.query(exists().where(MatrixDataSet.id == matrix_user_metadata.id)).scalar()
        if res:
            matrix_user_metadata = self.session.merge(matrix_user_metadata)
        else:
            self.session.add(matrix_user_metadata)
        self.session.commit()

        logger.debug(f"Matrix dataset {matrix_user_metadata.id} for user {matrix_user_metadata.owner_id} saved")
        return matrix_user_metadata

    def get(self, id_number: str) -> Optional[MatrixDataSet]:
        matrix: MatrixDataSet = self.session.query(MatrixDataSet).get(id_number)
        return matrix

    def get_all_datasets(self) -> List[MatrixDataSet]:
        matrix_datasets: List[MatrixDataSet] = self.session.query(MatrixDataSet).all()
        return matrix_datasets

    def query(
        self,
        name: Optional[str],
        owner: Optional[int] = None,
    ) -> List[MatrixDataSet]:
        """
        Query a list of MatrixUserMetadata by searching for each one separately if a set of filter match

        Parameters:
            name: the partial name of dataset
            owner: owner id to filter the result with

        Returns:
            the list of metadata per user, matching the query
        """
        query = self.session.query(MatrixDataSet)
        if name is not None:
            query = query.filter(MatrixDataSet.name.ilike(f"%{name}%"))  # type: ignore
        if owner is not None:
            query = query.filter(MatrixDataSet.owner_id == owner)
        datasets: List[MatrixDataSet] = query.distinct().all()
        return datasets

    def delete(self, dataset_id: str) -> None:
        dataset = self.session.query(MatrixDataSet).get(dataset_id)
        self.session.delete(dataset)
        self.session.commit()


class MatrixRepository:
    """
    Database connector to manage Matrix entity.
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def save(self, matrix: Matrix) -> Matrix:
        if self.session.query(exists().where(Matrix.id == matrix.id)).scalar():
            self.session.merge(matrix)
        else:
            self.session.add(matrix)
        self.session.commit()

        logger.debug(f"Matrix {matrix.id} saved")
        return matrix

    def get(self, matrix_hash: str) -> Optional[Matrix]:
        matrix: Matrix = self.session.query(Matrix).get(matrix_hash)
        return matrix

    def exists(self, matrix_hash: str) -> bool:
        res: bool = self.session.query(exists().where(Matrix.id == matrix_hash)).scalar()
        return res

    def delete(self, matrix_hash: str) -> None:
        if g := self.session.query(Matrix).get(matrix_hash):
            self.session.delete(g)
            self.session.commit()
        else:
            logger.warning(f"Trying to delete matrix {matrix_hash}, but was not found in database!")
        logger.debug(f"Matrix {matrix_hash} deleted")


@dataclass
class MatrixMetaData:
    hash: str
    new: bool


class MatrixContentRepository:
    """
    Manage the content of matrices stored in a directory.

    This class provides methods to get, check existence,
    save, and delete the content of matrices stored in a directory.
    The matrices are stored in various format (described in InternalMatrixFormat) and
    are accessed and modified using their SHA256 hash as their unique identifier.

    Attributes:
        bucket_dir: The directory path where the matrices are stored.
    """

    def __init__(self, bucket_dir: Path, format: InternalMatrixFormat) -> None:
        self.bucket_dir = bucket_dir
        self.bucket_dir.mkdir(parents=True, exist_ok=True)
        self.format = format

    def get(self, matrix_hash: str, matrix_version: int) -> pd.DataFrame:
        """
        Retrieves the content of a matrix with a given SHA256 hash.

        Parameters:
            matrix_hash: SHA256 hash
            matrix_version: The matrix version. Needed for parsing

        Returns:
            The matrix content or `None` if the file is not found.
        """
        for internal_format in InternalMatrixFormat:
            matrix_path = self.bucket_dir.joinpath(f"{matrix_hash}.{internal_format}")
            if matrix_path.exists():
                return load_matrix(internal_format, matrix_path, matrix_version)
        raise FileNotFoundError(str(self.bucket_dir.joinpath(matrix_hash)))

    def exists(self, matrix_hash: str) -> bool:
        """
        Checks if a matrix with a given SHA256 hash exists in the directory.

        Parameters:
            matrix_hash: SHA256 hash

        Returns:
            `True` if the matrix exist else `None`.
        """
        for internal_format in InternalMatrixFormat:
            matrix_path = self.bucket_dir.joinpath(f"{matrix_hash}.{internal_format}")
            if matrix_path.exists():
                return True
        return False

    def save(self, content: pd.DataFrame) -> MatrixMetaData:
        """
        The matrix content will be saved in the repository given format, where each row represents
        a line in the file and the values are separated by tabs. The file will be saved
        in the bucket directory using a unique filename. The SHA256 hash of the NumPy array
        is returned as a string.

        Parameters:
            content:
                The matrix content to be saved represented as a dataframe

        Returns:
            The SHA256 hash of the saved matrix file.

        Raises:
            ValueError:
                If the provided content is not a valid matrix or cannot be saved.
        """
        # IMPLEMENTATION DETAIL:
        # We chose to calculate the hash value from the binary data of the array buffer,
        # as this is much more efficient than using a JSON string conversion.
        # Note that in both cases, the hash value calculation is not stable:
        # 1. The same floating point number can have several possible representations
        #    depending on the platform on which the calculations are performed,
        # 2. The JSON conversion, necessarily involves a textual representation
        #    of the floating point numbers which can introduce rounding errors.
        # However, this method is still a good approach to calculate a hash value
        # for a non-mutable NumPy Array.
        matrix_hash = hashlib.sha256(np.ascontiguousarray(content.to_numpy()).data).hexdigest()
        matrix_path = self.bucket_dir.joinpath(f"{matrix_hash}.{self.format}")
        if matrix_path.exists():
            # Avoid having to save the matrix again (that's the whole point of using a hash).
            return MatrixMetaData(hash=matrix_hash, new=False)

        lock_file = matrix_path.with_suffix(".tsv.lock")  # use tsv lock to stay consistent with old data
        for internal_format in InternalMatrixFormat:
            matrix_in_another_format_path = self.bucket_dir.joinpath(f"{matrix_hash}.{internal_format}")
            if matrix_in_another_format_path.exists():
                # We want to migrate the old matrix in the given repository format.
                # Ensure exclusive access to the matrix file between multiple processes (or threads).
                with FileLock(lock_file, timeout=15):
                    save_matrix(self.format, content, matrix_path)
                    matrix_in_another_format_path.unlink()
                return MatrixMetaData(hash=matrix_hash, new=True)

        # Ensure exclusive access to the matrix file between multiple processes (or threads).
        with FileLock(lock_file, timeout=15):
            if content.empty:
                matrix_path.touch()
            else:
                save_matrix(self.format, content, matrix_path)

            # IMPORTANT: Deleting the lock file under Linux can make locking unreliable.
            # See https://github.com/tox-dev/py-filelock/issues/31
            # However, this deletion is possible when the matrix is no longer in use.
            # This is done in `MatrixGarbageCollector` when matrix files are deleted.

        return MatrixMetaData(hash=matrix_hash, new=True)

    def delete(self, matrix_hash: str) -> None:
        """
        Deletes the matrix file containing the content of a matrix with the given SHA256 hash.

        Parameters:
            matrix_hash: The SHA256 hash of the matrix.

        Raises:
            FileNotFoundError: If the matrix file does not exist.

        Note:
            This method also deletes any abandoned lock file.
        """
        possible_paths = [self.bucket_dir.joinpath(f"{matrix_hash}.{f}") for f in InternalMatrixFormat]
        if not any(path.exists() for path in possible_paths):
            raise FileNotFoundError(f"The matrix {matrix_hash} does not exist.")

        for internal_format in InternalMatrixFormat:
            matrix_path = self.bucket_dir.joinpath(f"{matrix_hash}.{internal_format}")
            matrix_path.unlink(missing_ok=True)

        # IMPORTANT: Deleting the lock file under Linux can make locking unreliable.
        # Abandoned lock files are deleted here to maintain consistent behavior.
        lock_file = matrix_path.with_suffix(".tsv.lock")
        lock_file.unlink(missing_ok=True)
