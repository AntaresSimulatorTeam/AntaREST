import contextlib
import io
import json
import logging
import tempfile
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np
import py7zr
from fastapi import UploadFile
from numpy import typing as npt

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.tasks.model import TaskResult, TaskType
from antarest.core.tasks.service import ITaskService, TaskUpdateNotifier
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch, zip_dir
from antarest.login.service import LoginService
from antarest.matrixstore.exceptions import MatrixDataSetNotFound
from antarest.matrixstore.model import (
    Matrix,
    MatrixContent,
    MatrixData,
    MatrixDataSet,
    MatrixDataSetDTO,
    MatrixDataSetRelation,
    MatrixDataSetUpdateDTO,
    MatrixDTO,
    MatrixInfoDTO,
)
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


class ISimpleMatrixService(ABC):
    @abstractmethod
    def create(self, data: Union[List[List[MatrixData]], npt.NDArray[np.float64]]) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get(self, matrix_id: str) -> Optional[MatrixDTO]:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, matrix_id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, matrix_id: str) -> None:
        raise NotImplementedError()


class SimpleMatrixService(ISimpleMatrixService):
    def __init__(self, bucket_dir: Path):
        self.bucket_dir = bucket_dir
        self.content_repo = MatrixContentRepository(bucket_dir)

    def create(self, data: Union[List[List[MatrixData]], npt.NDArray[np.float64]]) -> str:
        return self.content_repo.save(data)

    def get(self, matrix_id: str) -> MatrixDTO:
        data = self.content_repo.get(matrix_id)
        return MatrixDTO.construct(
            id=matrix_id,
            width=len(data.columns),
            height=len(data.index),
            index=data.index,
            columns=data.columns,
            data=data.data,
        )

    def exists(self, matrix_id: str) -> bool:
        return self.content_repo.exists(matrix_id)

    def delete(self, matrix_id: str) -> None:
        self.content_repo.delete(matrix_id)


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
        self.repo = repo
        self.repo_dataset = repo_dataset
        self.matrix_content_repository = matrix_content_repository
        self.user_service = user_service
        self.file_transfer_manager = file_transfer_manager
        self.task_service = task_service
        self.config = config

    @staticmethod
    def _from_dto(dto: MatrixDTO) -> Tuple[Matrix, MatrixContent]:
        matrix = Matrix(
            id=dto.id,
            width=dto.width,
            height=dto.height,
            created_at=datetime.fromtimestamp(dto.created_at),
        )

        content = MatrixContent(data=dto.data, index=dto.index, columns=dto.columns)

        return matrix, content

    def create(self, data: Union[List[List[MatrixData]], npt.NDArray[np.float64]]) -> str:
        """
        Creates a new matrix object with the specified data.

        - Saves the matrix data to the content repository.
        - Creates a new matrix object in the database, with metadata such as its width,
          height, and creation time.

        Parameters:
            data:
                The matrix content to be saved. It can be either a nested list of floats
                or a NumPy array of type np.float64.

        Returns:
            A SHA256 hash for the new matrix object.
            This identifier can be used to retrieve the matrix later.

        Important:
            If an error occurs while creating or saving the matrix object,
            the associated data file will not (and should not) be deleted.
            The `MatrixGarbageCollector` class is responsible for removing
            unreferenced matrices to avoid leaving unused files lying around.
        """
        matrix_id = self.matrix_content_repository.save(data)
        shape = data.shape if isinstance(data, np.ndarray) else (len(data), len(data[0]) if data else 0)
        with db():
            # Do not use the `timezone.utc` timezone to preserve a naive datetime.
            created_at = datetime.utcnow()
            matrix = Matrix(
                id=matrix_id,
                width=shape[1],
                height=shape[0],
                created_at=created_at,
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
            obj = json.loads(file)
            content = MatrixContent(**obj)
            return self.create(content.data)
        # noinspection PyTypeChecker
        matrix = np.loadtxt(io.BytesIO(file), delimiter="\t", dtype=np.float64, ndmin=2)
        matrix = matrix.reshape((1, 0)) if matrix.size == 0 else matrix
        return self.create(matrix)

    def get_dataset(
        self,
        id: str,
        params: RequestParameters,
    ) -> Optional[MatrixDataSet]:
        if not params.user:
            raise UserHasNotPermissionError()
        dataset = self.repo_dataset.get(id)
        if dataset is None:
            raise MatrixDataSetNotFound()

        MatrixService.check_access_permission(dataset, params.user, raise_error=True)
        return dataset

    def create_dataset(
        self,
        dataset_info: MatrixDataSetUpdateDTO,
        matrices: List[MatrixInfoDTO],
        params: RequestParameters,
    ) -> MatrixDataSet:
        if not params.user:
            raise UserHasNotPermissionError()

        groups = [self.user_service.get_group(group_id, params) for group_id in dataset_info.groups]
        dataset = MatrixDataSet(
            name=dataset_info.name,
            public=dataset_info.public,
            owner_id=params.user.impersonator,
            groups=groups,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        for matrix in matrices:
            matrix_relation = MatrixDataSetRelation(name=matrix.name)
            matrix_relation.matrix_id = matrix.id
            dataset.matrices.append(matrix_relation)

        return self.repo_dataset.save(dataset)

    def update_dataset(
        self,
        dataset_id: str,
        dataset_info: MatrixDataSetUpdateDTO,
        params: RequestParameters,
    ) -> MatrixDataSet:
        if not params.user:
            raise UserHasNotPermissionError()
        dataset = self.repo_dataset.get(dataset_id)
        if dataset is None:
            raise MatrixDataSetNotFound()
        MatrixService.check_access_permission(dataset, params.user, write=True, raise_error=True)
        groups = [self.user_service.get_group(group_id, params) for group_id in dataset_info.groups]
        updated_dataset = MatrixDataSet(
            id=dataset_id,
            name=dataset_info.name,
            public=dataset_info.public,
            groups=groups,
            updated_at=datetime.utcnow(),
        )
        return self.repo_dataset.save(updated_dataset)

    def list(
        self,
        dataset_name: Optional[str],
        filter_own: bool,
        params: RequestParameters,
    ) -> List[MatrixDataSetDTO]:
        """
        List matrix user metadata

        Parameters:
            dataset_name: the dataset name search query
            filter_own: indicate if only the current user datasets should be returned
            params: The request parameter containing user information

        Returns:
            the list of matching MatrixUserMetadata
        """
        user = params.user
        if not user:
            raise UserHasNotPermissionError()

        datasets = self.repo_dataset.query(dataset_name, user.impersonator if filter_own else None)
        return [
            dataset.to_dto()
            for dataset in datasets
            if dataset.public
            or user.is_or_impersonate(dataset.owner_id)
            or len([group for group in dataset.groups if group.id in [jwtgroup.id for jwtgroup in user.groups]]) > 0
        ]

    def delete_dataset(self, id: str, params: RequestParameters) -> str:
        if not params.user:
            raise UserHasNotPermissionError()

        dataset = self.repo_dataset.get(id)

        if dataset is None:
            raise MatrixDataSetNotFound()

        MatrixService.check_access_permission(dataset, params.user, write=True, raise_error=True)
        self.repo_dataset.delete(id)
        return id

    def get(self, matrix_id: str) -> Optional[MatrixDTO]:
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
            return None
        content = self.matrix_content_repository.get(matrix_id)
        return MatrixDTO.construct(
            id=matrix.id,
            width=matrix.width,
            height=matrix.height,
            created_at=int(matrix.created_at.timestamp()),
            index=content.index,
            columns=content.columns,
            data=content.data,
        )

    def exists(self, matrix_id: str) -> bool:
        """
        Check if a matrix object exists in both the matrix content repository and the database.

        Parameters:
            matrix_id: The SHA256 hash of the matrix object to check for existence.

        Returns:
            bool: `True` if the matrix object exists in both repositories, `False` otherwise.
        """
        return self.matrix_content_repository.exists(matrix_id) and self.repo.exists(matrix_id)

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
    def check_access_permission(
        dataset: MatrixDataSet,
        user: JWTUser,
        write: bool = False,
        raise_error: bool = False,
    ) -> bool:
        if user.is_site_admin():
            return True
        dataset_groups = [group.id for group in dataset.groups]
        access = (
            dataset.owner_id in [user.id, user.impersonator]
            or any(group.id in dataset_groups for group in user.groups)
            and not write
        )
        if not access and raise_error:
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
                filepath = f"{tmpdir}/{name}"
                array = np.array(mtx.data, dtype=np.float64)
                if array.size == 0:
                    # If the array or dataframe is empty, create an empty file instead of
                    # traditional saving to avoid unwanted line breaks.
                    open(filepath, mode="wb").close()
                else:
                    # noinspection PyTypeChecker
                    np.savetxt(filepath, array, delimiter="\t", fmt="%.18f")
            zip_dir(Path(tmpdir), export_path)
            stopwatch.log_elapsed(lambda x: logger.info(f"Matrix dataset exported (zipped mode) in {x}s"))
        return str(export_path)

    def download_dataset(
        self,
        dataset_id: str,
        params: RequestParameters,
    ) -> FileDownloadTaskDTO:
        """
        Export study output to a zip file.
        Parameters:
            dataset_id: matrix dataset id
            params: request parameters
        """
        if not params.user:
            raise UserHasNotPermissionError()
        dataset = self.repo_dataset.get(dataset_id)
        if dataset is None:
            raise MatrixDataSetNotFound()
        MatrixService.check_access_permission(dataset, params.user, raise_error=True)

        return self.download_matrix_list(
            [mtx_info.matrix_id for mtx_info in dataset.matrices],
            dataset.id,
            params,
        )

    def download_matrix_list(
        self,
        matrix_list: Sequence[str],
        dataset_name: str,
        params: RequestParameters,
    ) -> FileDownloadTaskDTO:
        logger.info(f"Exporting matrix dataset {dataset_name}")
        export_name = f"Exporting matrix dataset {dataset_name}"
        export_file_download = self.file_transfer_manager.request_download(
            f"matrixdataset-{dataset_name}.zip",
            export_name,
            params.user,
        )
        export_path = Path(export_file_download.path)
        export_id = export_file_download.id

        def export_task(notifier: TaskUpdateNotifier) -> TaskResult:
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
            export_task,
            export_name,
            task_type=TaskType.EXPORT,
            ref_id=None,
            custom_event_messages=None,
            request_params=params,
        )

        return FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)

    def download_matrix(
        self,
        matrix_id: str,
        filepath: Path,
        params: RequestParameters,
    ) -> None:
        """
        Prepare the matrix download if the user has permissions to do it.

        Parameters:
            matrix_id: The SHA256 hash of the matrix object to download.
            filepath: File path of the TSV file to write.
            params: Request parameters.
        """
        if not params.user:
            raise UserHasNotPermissionError()
        if matrix := self.get(matrix_id):
            array = np.array(matrix.data, dtype=np.float64)
            if array.size == 0:
                # If the array or dataframe is empty, create an empty file instead of
                # traditional saving to avoid unwanted line breaks.
                open(filepath, mode="wb").close()
            else:
                # noinspection PyTypeChecker
                np.savetxt(filepath, array, delimiter="\t", fmt="%.18f")
