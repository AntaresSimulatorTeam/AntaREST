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

import contextlib
import io
import logging
import tempfile
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Iterable, Iterator, List, Optional, Sequence

import numpy as np
import pandas as pd
import polars as pl
import py7zr
from fastapi import UploadFile
from polars import String
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
from antarest.core.utils.polars import create_polars_dataframe
from antarest.core.utils.utils import StopWatch, current_time
from antarest.login.service import LoginService
from antarest.login.utils import require_current_user
from antarest.matrixstore.exceptions import MatrixDataSetNotFound, MatrixNotFound, MatrixNotSupported
from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import (
    Matrix,
    MatrixContent,
    MatrixDataSet,
    MatrixDataSetDTO,
    MatrixDataSetRelation,
    MatrixDataSetUpdateDTO,
    MatrixDescriptionDTO,
    MatrixInfoDTO,
    MatrixMetadataDTO,
    MatrixMismatchDTO,
    MatrixReference,
    MatrixReferencesDTO,
)
from antarest.matrixstore.parsing import load_matrix, save_matrix
from antarest.matrixstore.repository import (
    MatrixContentRepository,
    MatrixDataSetRepository,
    MatrixRepository,
    compute_hash,
)

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
    @abstractmethod
    def add_predefined_matrix(self, matrix_factory: Callable[[], pl.DataFrame]) -> str:
        """
        Registers a predefined matrix which will not created with factory function when requested.

        This allows to not actually store often used matrices, and create them on the fly instead
        of reading them from storage.
        """
        raise NotImplementedError()

    @abstractmethod
    def create(self, data: pl.DataFrame) -> str:
        """
        Creates a new matrix object with the specified data.
        """
        raise NotImplementedError()

    @abstractmethod
    def create_batch(self, data: Iterator[pl.DataFrame]) -> list[str]:
        """
        Creates several matrices with the specified data.
        Returns the list of the created matrices ids.
        """
        raise NotImplementedError()

    @abstractmethod
    def get(self, matrix_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_matrices(self) -> list[MatrixMetadataDTO]:
        raise NotImplementedError()

    @abstractmethod
    def yield_matrices(self, matrix_ids: Sequence[str]) -> Iterator[MatrixContent]:
        """
        Returns an iterator over MatrixContent objects containing the matrix id and the dataframe it represents.
        """
        raise NotImplementedError()

    @abstractmethod
    def exists(self, matrix_id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, matrix_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def register_usage_provider(self, usage_provider: "IMatrixUsageProvider") -> None:
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
            return self.create(create_polars_dataframe(matrix))
        else:
            raise TypeError(f"Invalid type for matrix: {type(matrix)}")

    @abstractmethod
    def get_matrices_references(self, disk_usage: bool) -> dict[str, MatrixReferencesDTO]:
        raise NotImplementedError

    @abstractmethod
    def synchronize_matrix_store(self, dry_run: bool) -> dict[str, MatrixMismatchDTO]:
        raise NotImplementedError


class SimpleMatrixService(ISimpleMatrixService):
    def __init__(self, matrix_content_repository: MatrixContentRepository):
        self.matrix_content_repository = matrix_content_repository
        self.usage_providers: List[IMatrixUsageProvider] = []
        self._predefined_matrices: dict[str, Callable[[], pl.DataFrame]] = {}

    @override
    def add_predefined_matrix(self, matrix_factory: Callable[[], pl.DataFrame]) -> str:
        matrix_id = compute_hash(matrix_factory())
        self._predefined_matrices[matrix_id] = matrix_factory
        return matrix_id

    @override
    def create(self, data: pl.DataFrame) -> str:
        return self.matrix_content_repository.save(data).hash

    @override
    def create_batch(self, data: Iterator[pl.DataFrame]) -> list[str]:
        return [self.matrix_content_repository.save(df).hash for df in data]

    @override
    def get(self, matrix_id: str) -> pl.DataFrame:
        if matrix_id in self._predefined_matrices:
            return self._predefined_matrices[matrix_id]()
        return self.matrix_content_repository.get(matrix_id, matrix_version=NEW_MATRIX_VERSION)

    @override
    def get_matrices(self) -> list[MatrixMetadataDTO]:
        raise NotImplementedError()

    @override
    def yield_matrices(self, matrix_ids: Sequence[str]) -> Iterator[MatrixContent]:
        for matrix_id in matrix_ids:
            yield MatrixContent(id=matrix_id, data=self.get(matrix_id))

    @override
    def exists(self, matrix_id: str) -> bool:
        return matrix_id in self._predefined_matrices or self.matrix_content_repository.exists(matrix_id)

    @override
    def delete(self, matrix_id: str) -> None:
        self.matrix_content_repository.delete(matrix_id)

    @override
    def register_usage_provider(self, usage_provider: "IMatrixUsageProvider") -> None:
        self.usage_providers.append(usage_provider)

    @override
    def get_matrices_references(self, disk_usage: bool) -> dict[str, MatrixReferencesDTO]:
        raise NotImplementedError

    @override
    def synchronize_matrix_store(self, dry_run: bool) -> dict[str, MatrixMismatchDTO]:
        return {}


def check_dataframe_compliance(df: pl.DataFrame) -> None:
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
    if df.is_empty():
        return

    for dtype in df.dtypes:
        if not (dtype.is_numeric() or dtype.is_temporal() or dtype == String):
            raise MatrixNotSupported(
                f"Supported matrix data types are 'number, datetime, string' and you provided {dtype}"
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
        self.matrix_content_repository = matrix_content_repository
        self.repo = repo
        self.repo_dataset = repo_dataset
        self.user_service = user_service
        self.file_transfer_manager = file_transfer_manager
        self.task_service = task_service
        self.config = config
        self.usage_providers: List[IMatrixUsageProvider] = []
        self._create_dataset_usage_provider()
        self._predefined_matrices: dict[str, Callable[[], pl.DataFrame]] = {}

    @override
    def add_predefined_matrix(self, matrix_factory: Callable[[], pl.DataFrame]) -> str:
        matrix_id = compute_hash(matrix_factory())
        self._predefined_matrices[matrix_id] = matrix_factory
        return matrix_id

    def _create(self, data: pl.DataFrame) -> tuple[str, Matrix | None]:
        check_dataframe_compliance(data)
        matrix_metadata = self.matrix_content_repository.save(data)
        matrix_id = matrix_metadata.hash
        if not matrix_metadata.new:
            # Nothing to do
            return matrix_id, None
        created_at = current_time()
        matrix = Matrix(id=matrix_id, width=data.shape[1], height=data.shape[0], created_at=created_at, version=2)
        return matrix_id, matrix

    @override
    def create(self, data: pl.DataFrame) -> str:
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
            The matrix garbage collection Celery task is responsible for removing
            unreferenced matrices to avoid leaving unused files lying around.
        """
        matrix_id, matrix_model = self._create(data)
        if matrix_model is not None:
            self.repo.save(matrix_model)
        return matrix_id

    @override
    def create_batch(self, data: Iterator[pl.DataFrame]) -> list[str]:
        matrices = []
        matrices_ids = []
        for df in data:
            matrix_id, matrix_model = self._create(df)
            if matrix_model is not None:
                matrices.append(matrix_model)
            matrices_ids.append(matrix_id)
        self.repo.save_batch(matrices)
        return matrices_ids

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
            pandas_df = pd.DataFrame(data=obj["data"], index=obj["index"], columns=obj["columns"])
            return self.create(pl.from_pandas(pandas_df))
        # noinspection PyTypeChecker
        matrix = np.loadtxt(io.BytesIO(file), delimiter="\t", dtype=np.float64, ndmin=2)
        matrix = matrix.reshape((1, 0)) if matrix.size == 0 else matrix
        return self.create(create_polars_dataframe(matrix))

    def get_dataset(self, id: str) -> Optional[MatrixDataSet]:
        dataset = self.repo_dataset.get(id)
        if dataset is None:
            raise MatrixDataSetNotFound()

        MatrixService.check_access_permission(dataset)
        return dataset

    def create_dataset(self, dataset_info: MatrixDataSetUpdateDTO, matrices: List[MatrixInfoDTO]) -> MatrixDataSet:
        user = require_current_user()

        groups = [self.user_service.get_group(group_id) for group_id in dataset_info.groups]
        now_utc = current_time()
        dataset = MatrixDataSet(
            name=dataset_info.name,
            public=dataset_info.public,
            owner_id=user.impersonator,
            groups=groups,
            created_at=now_utc,
            updated_at=now_utc,
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
            updated_at=current_time(),
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
    def get(self, matrix_id: str) -> pl.DataFrame:
        """
        Get a matrix object from the database and the matrix content repository.

        Parameters:
            matrix_id: The SHA256 hash of the matrix object to search for.

        Returns:
            A Data Transfer Object (DTO) of the matrix and its content,
            or `None` if the matrix is not found in the database.
        """
        if matrix_id in self._predefined_matrices:
            return self._predefined_matrices[matrix_id]()
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
    def yield_matrices(self, matrix_ids: Sequence[str]) -> Iterator[MatrixContent]:
        # First yield predefined matrices
        db_matrix_ids = []
        for matrix_id in matrix_ids:
            if matrix_id in self._predefined_matrices:
                yield MatrixContent(id=matrix_id, data=self._predefined_matrices[matrix_id]())
            else:
                db_matrix_ids.append(matrix_id)
        # Then fetch the other ones in DB
        if db_matrix_ids:
            matrices = self.repo.get_batch(db_matrix_ids)
            for matrix in matrices:
                yield MatrixContent(id=matrix.id, data=self.matrix_content_repository.get(matrix.id, matrix.version))

    @override
    def exists(self, matrix_id: str) -> bool:
        """
        Check if a matrix object exists in both the matrix content repository and the database.

        Parameters:
            matrix_id: The SHA256 hash of the matrix object to check for existence.

        Returns:
            bool: `True` if the matrix object exists in both repositories, `False` otherwise.
        """
        return matrix_id in self._predefined_matrices or (
            self.matrix_content_repository.exists(matrix_id) and self.repo.exists(matrix_id)
        )

    @override
    def delete(self, matrix_id: str) -> None:
        """
        Delete a matrix object from the matrix content repository and the database.

        Parameters:
            matrix_id: The SHA256 hash of the matrix object to delete.
        """
        # Matrix deletion is done exclusively when the matrix garbage collection
        # Celery task collects deprecated matrices (matrices that are no longer
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

    @override
    def register_usage_provider(self, usage_provider: "IMatrixUsageProvider") -> None:
        self.usage_providers.append(usage_provider)

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

    def get_used_matrices(self) -> Iterable[MatrixReference]:
        """Return all matrices used in raw studies, variant studies, constants hashes, variables views and datasets"""
        for provider in self.usage_providers:
            yield from provider.get_matrix_usage()

    def _create_dataset_usage_provider(self) -> "IMatrixUsageProvider":
        repo_dataset = self.repo_dataset

        class DatasetUsageProvider(IMatrixUsageProvider):
            def __init__(self, matrix_service: "MatrixService") -> None:
                matrix_service.register_usage_provider(self)

            @override
            def get_matrix_usage(self) -> Iterable[MatrixReference]:
                logger.info("Getting all matrices used in datasets")
                datasets = repo_dataset.get_all_datasets()

                for dataset in datasets:
                    for matrix in dataset.matrices:
                        yield MatrixReference(
                            matrix_id=matrix.matrix_id, use_description=f"Used by dataset {dataset.id}"
                        )

        return DatasetUsageProvider(self)

    @override
    def get_matrices_references(self, disk_usage: bool) -> dict[str, MatrixReferencesDTO]:
        used_matrices = self.get_used_matrices()
        references_dto: dict[str, MatrixReferencesDTO] = {}
        for matrix in used_matrices:
            matrix_size = None
            matrix_id = matrix.matrix_id

            ref_dto = MatrixDescriptionDTO(description=matrix.use_description)

            if matrix_id not in references_dto:
                if disk_usage:
                    matrix_size = self.matrix_content_repository.get_matrix_disk_usage(matrix_id)

                refs_dto = MatrixReferencesDTO(refs=[ref_dto], disk_usage=matrix_size)
                references_dto.update({matrix_id: refs_dto})
            else:
                references_dto[matrix_id].refs.append(ref_dto)

        return references_dto

    @override
    def synchronize_matrix_store(self, dry_run: bool) -> dict[str, MatrixMismatchDTO]:
        db_matrices = {m.id for m in self.repo.get_matrices()}
        fs_matrices = {
            f.stem for f in self.matrix_content_repository.bucket_dir.iterdir() if not f.name.endswith(".tsv.lock")
        }
        only_fs_matrices = fs_matrices - db_matrices
        only_db_matrices = db_matrices - fs_matrices

        result = {}
        for matrix in only_db_matrices:
            result[matrix] = MatrixMismatchDTO(database=True, filesystem=False)
            if not dry_run:
                # We remove the line from DB as it has no match on the filesystem
                self.repo.delete(matrix)

        new_matrices = []
        current_date = current_time()
        for matrix in only_fs_matrices:
            result[matrix] = MatrixMismatchDTO(database=False, filesystem=True)
            if not dry_run:
                # We have to create a fake entry for the matrix in DB to fit with the filesystem.
                # But for that we have to find what's the matrix version as it's used for parsing.
                version = self._infer_matrix_version(matrix)
                obj = Matrix(id=matrix, width=10, height=10, created_at=current_date, version=version)
                new_matrices.append(obj)

        if new_matrices:
            self.repo.save_batch(new_matrices)

        return result

    def _infer_matrix_version(self, matrix_id: str) -> int:
        matrix_path, matrix_format = self.matrix_content_repository.get_matrix_path_n_format(matrix_id)
        assert matrix_path is not None

        if matrix_format != InternalMatrixFormat.TSV:
            # We only need the matrix version for the parsing of legacy `TSV` files.
            return NEW_MATRIX_VERSION

        df = load_matrix(matrix_format, matrix_path, LEGACY_MATRIX_VERSION)
        new_hash = compute_hash(df)
        if new_hash == matrix_id:
            # Means we read the matrix as we supposed to so the version we tested was right
            return LEGACY_MATRIX_VERSION
        else:
            # Means we did not read the matrix as we were supposed to so we have to return the other version
            return NEW_MATRIX_VERSION
