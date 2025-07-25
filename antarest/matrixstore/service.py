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

import contextlib
import io
import logging
import tempfile
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np
import pandas as pd
import py7zr
from fastapi import UploadFile
from pandas.api.types import infer_dtype
from typing_extensions import override

from antarest.core.config import Config, InternalMatrixFormat
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.serde.json import from_json
from antarest.core.tasks.model import TaskResult, TaskType
from antarest.core.tasks.service import ITaskNotifier, ITaskService
from antarest.core.utils.archives import ArchiveFormat, archive_dir
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch
from antarest.login.service import LoginService
from antarest.login.utils import require_current_user
from antarest.matrixstore.exceptions import MatrixDataSetNotFound, MatrixNotFound, MatrixNotSupported
from antarest.matrixstore.model import (
    Matrix,
    MatrixDataSet,
    MatrixDataSetDTO,
    MatrixDataSetRelation,
    MatrixDataSetUpdateDTO,
    MatrixInfoDTO,
    MatrixMetadataDTO,
)
from antarest.matrixstore.parsing import save_matrix
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository

# List of files to exclude from ZIP archives
EXCLUDED_FILES = {
    "__MACOSX",
    ".DS_Store",
    "._.DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "$RECYCLE.BIN",
    "System Volume Information",
    "RECYCLER",
}

logger = logging.getLogger(__name__)

MATRIX_PROTOCOL_PREFIX = "matrix://"

LEGACY_MATRIX_VERSION = 1
NEW_MATRIX_VERSION = 2
"""
Version 1 matrices were not saved with a header, unlike version 2 ones.
Therefore, we rely on this version to know how to read the matrices
"""


class ISimpleMatrixService(ABC):
    def __init__(self, matrix_content_repository: MatrixContentRepository) -> None:
        self.matrix_content_repository = matrix_content_repository

    @abstractmethod
    def create(self, data: pd.DataFrame) -> str:
        """
        Creates a new matrix object with the specified data.

        Warning:
            DataFrame indexes are ignored, therefore providing one with a non-default one will raise an exception.
        """
        raise NotImplementedError()

    @abstractmethod
    def get(self, matrix_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_matrices(self) -> list[MatrixMetadataDTO]:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, matrix_id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, matrix_id: str) -> None:
        raise NotImplementedError()

    def get_matrix_id(self, matrix: List[List[float]] | str) -> str:
        """
        Get the matrix ID from a matrix or a matrix link.

        Args:
            matrix: The matrix or matrix link to get the ID from.

        Returns:
            The matrix ID.

        Raises:
            TypeError: If the provided matrix is neither a matrix nor a link to a matrix.
        """
        # noinspection SpellCheckingInspection
        if isinstance(matrix, str):
            return matrix.removeprefix(MATRIX_PROTOCOL_PREFIX)
        elif isinstance(matrix, list):
            return self.create(pd.DataFrame(data=matrix))
        else:
            raise TypeError(f"Invalid type for matrix: {type(matrix)}")


class SimpleMatrixService(ISimpleMatrixService):
    def __init__(self, matrix_content_repository: MatrixContentRepository):
        super().__init__(matrix_content_repository=matrix_content_repository)

    @override
    def create(self, data: pd.DataFrame) -> str:
        return self.matrix_content_repository.save(data).hash

    @override
    def get(self, matrix_id: str) -> pd.DataFrame:
        return self.matrix_content_repository.get(matrix_id, matrix_version=NEW_MATRIX_VERSION)

    @override
    def get_matrices(self) -> list[MatrixMetadataDTO]:
        raise NotImplementedError()

    @override
    def exists(self, matrix_id: str) -> bool:
        return self.matrix_content_repository.exists(matrix_id)

    @override
    def delete(self, matrix_id: str) -> None:
        self.matrix_content_repository.delete(matrix_id)


def check_dataframe_compliance(df: pd.DataFrame) -> None:
    """
    Checks compliance with the matrix store assumptions.

     - Only supported types for now are numbers, datetimes, and strings.
     - Because the matrix store ignores indexes, we check that the index
      is actually the default index.

    Notes:
    pd.StringDType is considered experimental and not supported everywhere, for example
    by to_hdf5, therefore we use `infer_dtype` to check object dtype are actually
    strings.
    """
    if df.empty:
        return

    if not df.index.equals(pd.RangeIndex(0, df.shape[0])):
        raise MatrixNotSupported("The matrixstore doesn't support dataframes with a non-default index")

    supported_dtypes = [np.number, np.datetime64]
    for k, dtype in enumerate(list(df.dtypes)):
        if not any(np.issubdtype(dtype.type, supported_type) for supported_type in supported_dtypes):
            if infer_dtype(df[df.columns[k]]) != "string":
                raise MatrixNotSupported(
                    f"Supported matrix data types are 'string, np.number, datetime' and you provided {dtype}"
                )


def _matrix_to_dto(matrix: Matrix) -> MatrixMetadataDTO:
    matrix_model = MatrixMetadataDTO(
        id=matrix.id, width=matrix.width, height=matrix.height, created_at=matrix.created_at, version=matrix.version
    )

    return matrix_model


class MatrixService(ISimpleMatrixService):
    def __init__(
        self,
        repo: MatrixRepository,
        repo_dataset: MatrixDataSetRepository,
        matrix_content_repository: MatrixContentRepository,
        file_transfer_manager: FileTransferManager,
        task_service: ITaskService,
        config: Config,
        user_service: LoginService,
    ):
        super().__init__(matrix_content_repository=matrix_content_repository)
        self.repo = repo
        self.repo_dataset = repo_dataset
        self.user_service = user_service
        self.file_transfer_manager = file_transfer_manager
        self.task_service = task_service
        self.config = config

    @override
    def create(self, data: pd.DataFrame) -> str:
        """
        Creates a new matrix object with the specified data.

        - Saves the matrix data to the content repository.
        - Creates a new matrix object in the database, with metadata such as its width,
          height, and creation time.

        Parameters:
            data:
                The matrix content to be saved. Note that the index is ignored by
                the matrix store, hence all non-default index will be rejected.
                Only numeric, datetime, and string content are supported.

        Returns:
            A SHA256 hash for the new matrix object.
            This identifier can be used to retrieve the matrix later.

        Important:
            If an error occurs while creating or saving the matrix object,
            the associated data file will not (and should not) be deleted.
            The `MatrixGarbageCollector` class is responsible for removing
            unreferenced matrices to avoid leaving unused files lying around.
        """
        check_dataframe_compliance(data)
        matrix_metadata = self.matrix_content_repository.save(data)
        matrix_id = matrix_metadata.hash
        if not matrix_metadata.new:
            # Nothing to change inside the DB
            return matrix_id
        else:
            with db():
                # Do not use the `timezone.utc` timezone to preserve a naive datetime.
                created_at = datetime.utcnow()
                matrix = Matrix(
                    id=matrix_id, width=data.shape[1], height=data.shape[0], created_at=created_at, version=2
                )
                self.repo.save(matrix)
        return matrix_id

    def create_by_importation(self, file: UploadFile, is_json: bool = False) -> List[MatrixInfoDTO]:
        """
        Imports a matrix from a TSV or JSON file or a collection of matrices from a ZIP file.

        TSV-formatted files are expected to contain only matrix data without any header.

        JSON-formatted files are expected to contain the following attributes:

        - `index`: The list of row labels.
        - `columns`: The list of column labels.
        - `data`: The matrix data as a nested list of floats.

        Args:
            file: The file to import (TSV, JSON or ZIP).
            is_json: Flag indicating if the file is JSON-encoded.

        Returns:
            A list of `MatrixInfoDTO` objects containing the SHA256 hash of the imported matrices.
        """
        with file.file as f:
            assert file.filename is not None
            if file.content_type == "application/zip":
                with contextlib.closing(f):
                    buffer = io.BytesIO(f.read())
                matrix_info: List[MatrixInfoDTO] = []
                if file.filename.endswith("zip"):
                    with zipfile.ZipFile(buffer) as zf:
                        for info in zf.infolist():
                            if info.is_dir() or info.filename in EXCLUDED_FILES:
                                continue
                            matrix_id = self._file_importation(zf.read(info.filename), is_json=is_json)
                            matrix_info.append(MatrixInfoDTO(id=matrix_id, name=info.filename))
                else:
                    with py7zr.SevenZipFile(buffer, "r") as szf:
                        for info in szf.list():
                            if info.is_directory or info.filename in EXCLUDED_FILES:  # type:ignore
                                continue
                            file_content = next(iter(szf.read(info.filename).values()))
                            matrix_id = self._file_importation(file_content.read(), is_json=is_json)
                            matrix_info.append(MatrixInfoDTO(id=matrix_id, name=info.filename))
                            szf.reset()
                return matrix_info
            else:
                matrix_id = self._file_importation(f.read(), is_json=is_json)
                return [MatrixInfoDTO(id=matrix_id, name=file.filename)]

    def _file_importation(self, file: bytes, *, is_json: bool = False) -> str:
        """
        Imports a matrix from a TSV or JSON file in bytes format.

        Parameters:
            file: The file contents as bytes.
            is_json: `True` if the file is JSON-encoded (default: `False`).

        Returns:
            A SHA256 hash that identifies the imported matrix.
        """
        if is_json:
            obj = from_json(file)
            df = pd.DataFrame(data=obj["data"], index=obj["index"], columns=obj["columns"])
            return self.create(df)
        # noinspection PyTypeChecker
        matrix = np.loadtxt(io.BytesIO(file), delimiter="\t", dtype=np.float64, ndmin=2)
        matrix = matrix.reshape((1, 0)) if matrix.size == 0 else matrix
        return self.create(pd.DataFrame(data=matrix))

    def get_dataset(self, id: str) -> Optional[MatrixDataSet]:
        dataset = self.repo_dataset.get(id)
        if dataset is None:
            raise MatrixDataSetNotFound()

        MatrixService.check_access_permission(dataset)
        return dataset

    def create_dataset(self, dataset_info: MatrixDataSetUpdateDTO, matrices: List[MatrixInfoDTO]) -> MatrixDataSet:
        user = require_current_user()

        groups = [self.user_service.get_group(group_id) for group_id in dataset_info.groups]
        dataset = MatrixDataSet(
            name=dataset_info.name,
            public=dataset_info.public,
            owner_id=user.impersonator,
            groups=groups,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        for matrix in matrices:
            matrix_relation = MatrixDataSetRelation(name=matrix.name)
            matrix_relation.matrix_id = matrix.id
            dataset.matrices.append(matrix_relation)

        return self.repo_dataset.save(dataset)

    def update_dataset(self, dataset_id: str, dataset_info: MatrixDataSetUpdateDTO) -> MatrixDataSet:
        dataset = self.repo_dataset.get(dataset_id)
        if dataset is None:
            raise MatrixDataSetNotFound()
        MatrixService.check_access_permission(dataset, write=True)
        groups = [self.user_service.get_group(group_id) for group_id in dataset_info.groups]
        updated_dataset = MatrixDataSet(
            id=dataset_id,
            name=dataset_info.name,
            public=dataset_info.public,
            groups=groups,
            updated_at=datetime.utcnow(),
        )
        return self.repo_dataset.save(updated_dataset)

    def list(self, dataset_name: Optional[str], filter_own: bool) -> List[MatrixDataSetDTO]:
        """
        List matrix user metadata

        Parameters:
            dataset_name: the dataset name search query
            filter_own: indicate if only the current user datasets should be returned

        Returns:
            the list of matching MatrixUserMetadata
        """
        user = require_current_user()

        datasets = self.repo_dataset.query(dataset_name, user.impersonator if filter_own else None)
        return [
            dataset.to_dto()
            for dataset in datasets
            if dataset.public
            or user.is_or_impersonate(dataset.owner_id)
            or len([group for group in dataset.groups if group.id in [jwtgroup.id for jwtgroup in user.groups]]) > 0
        ]

    def delete_dataset(self, id: str) -> str:
        dataset = self.repo_dataset.get(id)

        if dataset is None:
            raise MatrixDataSetNotFound()

        MatrixService.check_access_permission(dataset, write=True)
        self.repo_dataset.delete(id)
        return id

    @override
    def get(self, matrix_id: str) -> pd.DataFrame:
        """
        Get a matrix object from the database and the matrix content repository.

        Parameters:
            matrix_id: The SHA256 hash of the matrix object to search for.

        Returns:
            A Data Transfer Object (DTO) of the matrix and its content,
            or `None` if the matrix is not found in the database.
        """
        matrix = self.repo.get(matrix_id)
        if matrix is None:
            raise MatrixNotFound(matrix_id)
        return self.matrix_content_repository.get(matrix_id, matrix.version)

    @override
    def get_matrices(self) -> List[MatrixMetadataDTO]:
        """
        Get a list of matrix objects from the database
        Returns:#
            A list of matrices of the repository
        """

        matrices = self.repo.get_matrices()
        return [_matrix_to_dto(m) for m in matrices]

    @override
    def exists(self, matrix_id: str) -> bool:
        """
        Check if a matrix object exists in both the matrix content repository and the database.

        Parameters:
            matrix_id: The SHA256 hash of the matrix object to check for existence.

        Returns:
            bool: `True` if the matrix object exists in both repositories, `False` otherwise.
        """
        return self.matrix_content_repository.exists(matrix_id) and self.repo.exists(matrix_id)

    @override
    def delete(self, matrix_id: str) -> None:
        """
        Delete a matrix object from the matrix content repository and the database.

        Parameters:
            matrix_id: The SHA256 hash of the matrix object to delete.
        """
        # Matrix deletion is done exclusively when the `MatrixGarbageCollector`
        # service collects deprecated matrices (matrices that are no longer
        # used by any study) and deletes them.
        # So, we can ignore missing database records and/or missing files.
        # Currently, the deletion is done matrix by matrix (eager deletion
        # is not used, which is under-performing).
        # In the case of a unitary deletion, it is preferable to use a transaction
        # in order to have a rollback in case of failure, and to start with the
        # database deletion and finish with the file deletion (considered as atomic).
        with db():
            self.repo.delete(matrix_id)
            with contextlib.suppress(FileNotFoundError):
                self.matrix_content_repository.delete(matrix_id)

    @staticmethod
    def check_access_permission(dataset: MatrixDataSet, write: bool = False) -> bool:
        user = require_current_user()
        if user.is_site_admin():
            return True
        dataset_groups = [group.id for group in dataset.groups]
        access = (
            dataset.owner_id in [user.id, user.impersonator]
            or any(group.id in dataset_groups for group in user.groups)
            and not write
        )
        if not access:
            raise UserHasNotPermissionError()
        return access

    def create_matrix_files(self, matrix_ids: Sequence[str], export_path: Path) -> str:
        with tempfile.TemporaryDirectory(dir=self.config.storage.tmp_dir) as tmpdir:
            stopwatch = StopWatch()
            for mid in matrix_ids:
                mtx = self.get(mid)
                if not mtx:
                    continue
                name = f"matrix-{mtx.id}.txt"
                filepath = Path(tmpdir).joinpath(name)
                array = np.array(mtx.data, dtype=np.float64)
                if array.size == 0:
                    # If the array or dataframe is empty, create an empty file instead of
                    # traditional saving to avoid unwanted line breaks.
                    filepath.touch()
                else:
                    # noinspection PyTypeChecker
                    np.savetxt(filepath, array, delimiter="\t", fmt="%.18f")
            archive_dir(Path(tmpdir), export_path, archive_format=ArchiveFormat.ZIP)
            stopwatch.log_elapsed(lambda x: logger.info(f"Matrix dataset exported (zipped mode) in {x}s"))
        return str(export_path)

    def download_dataset(self, dataset_id: str) -> FileDownloadTaskDTO:
        """
        Export study output to a zip file.
        Parameters:
            dataset_id: matrix dataset id
        """
        dataset = self.repo_dataset.get(dataset_id)
        if dataset is None:
            raise MatrixDataSetNotFound()
        MatrixService.check_access_permission(dataset)

        return self.download_matrix_list([mtx_info.matrix_id for mtx_info in dataset.matrices], dataset.id)

    def download_matrix_list(self, matrix_list: Sequence[str], dataset_name: str) -> FileDownloadTaskDTO:
        logger.info(f"Exporting matrix dataset {dataset_name}")
        export_name = f"Exporting matrix dataset {dataset_name}"
        export_file_download = self.file_transfer_manager.request_download(
            f"matrixdataset-{dataset_name}.zip", export_name
        )
        export_path = Path(export_file_download.path)
        export_id = export_file_download.id

        def export_task(notifier: ITaskNotifier) -> TaskResult:
            try:
                self.create_matrix_files(matrix_ids=matrix_list, export_path=export_path)
                self.file_transfer_manager.set_ready(export_id)
                return TaskResult(
                    success=True,
                    message=f"Matrix dataset {dataset_name} successfully exported",
                )
            except Exception as e:
                self.file_transfer_manager.fail(export_id, str(e))
                raise e

        task_id = self.task_service.add_task(
            export_task, export_name, task_type=TaskType.EXPORT, ref_id=None, progress=None, custom_event_messages=None
        )

        return FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)

    def download_matrix(self, matrix_id: str, filepath: Path) -> None:
        """
        Prepare the matrix download if the user has permissions to do it.

        Parameters:
            matrix_id: The SHA256 hash of the matrix object to download.
            filepath: File path of the TSV file to write.
        """
        matrix = self.get(matrix_id)
        save_matrix(InternalMatrixFormat.TSV, matrix, filepath)
