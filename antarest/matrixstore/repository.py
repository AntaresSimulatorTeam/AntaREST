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
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import polars as pl
from filelock import FileLock
from pandas import util
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
        stmt = select(MatrixDataSet).where(MatrixDataSet.id == matrix_user_metadata.id)
        existing = self.session.scalar(stmt)

        if existing:
            matrix_user_metadata = self.session.merge(matrix_user_metadata)
        else:
            self.session.add(matrix_user_metadata)

        self.session.commit()
        logger.debug(f"Matrix dataset {matrix_user_metadata.id} for user {matrix_user_metadata.owner_id} saved")
        return matrix_user_metadata

    def get(self, id_number: str) -> Optional[MatrixDataSet]:
        return self.session.get(MatrixDataSet, id_number)

    def get_all_datasets(self) -> List[MatrixDataSet]:
        stmt = select(MatrixDataSet)
        result = self.session.execute(stmt)
        matrix_datasets: List[MatrixDataSet] = list(result.scalars().all())
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
        stmt = select(MatrixDataSet)
        if name is not None:
            stmt = stmt.where(MatrixDataSet.name.ilike(f"%{name}%"))
        if owner is not None:
            stmt = stmt.where(MatrixDataSet.owner_id == owner)
        result = self.session.execute(stmt.distinct())
        datasets: List[MatrixDataSet] = list(result.scalars().all())
        return datasets

    def delete(self, dataset_id: str) -> None:
        dataset = self.session.get(MatrixDataSet, dataset_id)
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
        existing = self.session.get(Matrix, matrix.id)

        if existing:
            merged_matrix = self.session.merge(matrix)
        else:
            self.session.add(matrix)
            merged_matrix = matrix

        self.session.commit()
        return merged_matrix

    def save_batch(self, matrices: list[Matrix]) -> None:
        try:
            self.session.add_all(matrices)
            self.session.commit()
        except IntegrityError:
            # Can happen if one the matrices is already inside DB.
            self.session.rollback()
            for matrix in matrices:
                self.save(matrix)

    def get(self, matrix_hash: str) -> Optional[Matrix]:
        return self.session.get(Matrix, matrix_hash)

    def get_matrices(self) -> list[Matrix]:
        return list(self.session.scalars(select(Matrix)))

    def get_batch(self, matrix_hashes: list[str]) -> list[Matrix]:
        return list(self.session.scalars(select(Matrix).filter(Matrix.id.in_(matrix_hashes))))

    def exists(self, matrix_hash: str) -> bool:
        result = self.session.get(Matrix, matrix_hash)
        return result is not None

    def delete(self, matrix_hash: str) -> None:
        matrix = self.session.get(Matrix, matrix_hash)
        if matrix:
            self.session.delete(matrix)
            self.session.commit()
            logger.debug(f"Matrix {matrix_hash} deleted")
        else:
            logger.warning(f"Trying to delete matrix {matrix_hash}, but was not found in database!")


@dataclass(frozen=True)
class MatrixCreationResult:
    hash: str
    new: bool


def compute_hash(df: pl.DataFrame) -> str:
    """
    Computes a hash of the dataframe, with the goal of obtaining a stable
    and unique identifier for its content, including the headers.

    The index is not considered, since the matrix store ignores it.

    For the implementation, we rely on:

    - pandas hash_pandas_object to compute int64 hashes for whole rows and for the
      column names
    - sha256 algo to hash the concatenation of those 2 "list" of hashes

    The hash could probably be improved by including more details, like
    the type of the column, the shape of the matrix ... It has not been
    considered necessary.

    Legacy implementation assumed the data was only numeric, since the
    matrix store only managed numeric data. It was only based on the hash
    of the numpy raw data, which was quite weak since 2 arrays with the
    same content but different shapes would have conflicting hashes.

    Still, the legacy implementation is still used for backwards compatibility,
    for numeric-only tables.
    """
    df = df.to_pandas()
    # Checks dataframe dtype to infer if the matrix could correspond to a legacy format
    legacy_format = False
    if all(np.issubdtype(dtype.type, np.number) for dtype in df.dtypes):
        # We also need to check the headers to see if they correspond to the default ones
        if df.columns.equals(pd.RangeIndex(0, df.shape[1])):
            legacy_format = True

    if not legacy_format:
        # We're computing the hash with the dataframe content and its headers
        column_names_hashes = util.hash_pandas_object(df.columns, index=False)
        row_hashes = util.hash_pandas_object(df, index=False)
        df_hash = hashlib.sha256(column_names_hashes.to_numpy(dtype=np.int64).data)
        df_hash.update(row_hashes.to_numpy(dtype=np.int64).data)
        return df_hash.hexdigest()

    # We're using `np.ascontiguousarray` as hashlib requires C contiguous arrays,
    # while this is not the general behaviour of pandas to store its data this way
    return hashlib.sha256(np.ascontiguousarray(df.to_numpy(dtype=np.float64)).data).hexdigest()


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

    def get(self, matrix_hash: str, matrix_version: int) -> pl.DataFrame:
        """
        Retrieves the content of a matrix with a given SHA256 hash.

        Parameters:
            matrix_hash: SHA256 hash
            matrix_version: The matrix version. Needed for parsing

        Returns:
            The matrix content or `None` if the file is not found.
        """
        matrix_path, internal_format = self._get_matrix_path_n_format(matrix_hash)
        if matrix_path:
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
        matrix_path = self._get_matrix_path_n_format(matrix_hash)[0]
        if matrix_path:
            return True
        return False

    def save(self, content: pl.DataFrame) -> MatrixCreationResult:
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

        matrix_hash = compute_hash(content)
        matrix_path = self.bucket_dir.joinpath(f"{matrix_hash}.{self.format}")

        # First check for the fast path without locking
        if matrix_path.exists():
            # Avoid having to save the matrix again (that's the whole point of using a hash).
            return MatrixCreationResult(hash=matrix_hash, new=False)

        # Ensure exclusive access to the matrix file between multiple processes (or threads).
        lock_file = matrix_path.with_suffix(".tsv.lock")  # use tsv lock to stay consistent with old data
        with FileLock(lock_file, timeout=15):
            # we check again for the existence of the file, as it might have been created by another process or thread
            if matrix_path.exists():
                # Avoid having to save the matrix again (that's the whole point of using a hash).
                return MatrixCreationResult(hash=matrix_hash, new=False)

            other_formats = [f for f in InternalMatrixFormat if f != self.format]
            for internal_format in other_formats:
                matrix_in_another_format_path = self.bucket_dir.joinpath(f"{matrix_hash}.{internal_format}")
                if matrix_in_another_format_path.exists():
                    # We want to migrate the old matrix in the given repository format.
                    # Ensure exclusive access to the matrix file between multiple processes (or threads).
                    save_matrix(self.format, content, matrix_path)
                    matrix_in_another_format_path.unlink()
                    return MatrixCreationResult(hash=matrix_hash, new=True)

            save_matrix(self.format, content, matrix_path)

            # IMPORTANT: Deleting the lock file under Linux can make locking unreliable.
            # See https://github.com/tox-dev/py-filelock/issues/31
            # However, this deletion is possible when the matrix is no longer in use.
            # This is done by the matrix garbage collection Celery task when matrix files are deleted.

            return MatrixCreationResult(hash=matrix_hash, new=True)

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

    def get_matrix_disk_usage(self, matrix_hash: str) -> int:
        matrix_path = self._get_matrix_path_n_format(matrix_hash)[0]
        if matrix_path:
            return os.stat(matrix_path).st_size
        raise FileNotFoundError(str(self.bucket_dir.joinpath(matrix_hash)))

    def _get_matrix_path_n_format(self, matrix_hash: str) -> tuple[Optional[Path], InternalMatrixFormat]:
        for internal_format in InternalMatrixFormat:
            matrix_path = self.bucket_dir.joinpath(f"{matrix_hash}.{internal_format}")
            if matrix_path.exists():
                return matrix_path, internal_format

        return None, InternalMatrixFormat.HDF
