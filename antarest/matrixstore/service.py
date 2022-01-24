import logging
import os
import shutil
import tempfile
import time
from abc import abstractmethod, ABC
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple
from zipfile import ZipFile

from fastapi import UploadFile

from antarest.core.config import StorageConfig, Config
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.jwt import JWTUser
from antarest.core.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.core.tasks.model import TaskResult
from antarest.core.tasks.service import (
    TaskUpdateNotifier,
    ITaskService,
    TaskType,
)
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch
from antarest.login.service import LoginService
from antarest.matrixstore.exceptions import MatrixDataSetNotFound
from antarest.matrixstore.model import (
    MatrixDTO,
    Matrix,
    MatrixContent,
    MatrixDataSet,
    MatrixDataSetUpdateDTO,
    MatrixDataSetDTO,
    MatrixInfoDTO,
    MatrixDataSetRelation,
    MatrixData,
)
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
    MatrixDataSetRepository,
)
from antarest.matrixstore.utils import (
    parse_tsv_matrix,
    write_tsv_matrix,
    write_tsv_matrix_to_file,
)

logger = logging.getLogger(__name__)


class ISimpleMatrixService(ABC):
    @abstractmethod
    def create(self, data: List[List[MatrixData]]) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get(self, id: str) -> Optional[MatrixDTO]:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, id: str) -> None:
        raise NotImplementedError()


class SimpleMatrixService(ISimpleMatrixService):
    def __init__(self, matrix_path: Path):
        self.matrix_path = matrix_path
        assert matrix_path.exists() and matrix_path.is_dir()
        config = Config(storage=StorageConfig(matrixstore=matrix_path))
        self.matrix_content_repository = MatrixContentRepository(config)

    def create(self, data: List[List[MatrixData]]) -> str:
        matrix_hash = self.matrix_content_repository.save(data)
        return matrix_hash

    def get(self, id: str) -> Optional[MatrixDTO]:
        data = self.matrix_content_repository.get(id)
        if data:
            assert data.columns is not None
            assert data.index is not None
            return MatrixDTO(
                id=id,
                width=len(data.columns),
                height=len(data.index),
                index=data.index,
                columns=data.columns,
                data=data.data,
            )
        else:
            return None

    def exists(self, id: str) -> bool:
        return self.matrix_content_repository.exists(id)

    def delete(self, id: str) -> None:
        self.matrix_content_repository.delete(id)


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
    def _to_dto(matrix: Matrix, content: MatrixContent) -> MatrixDTO:
        return MatrixDTO(
            id=matrix.id,
            width=matrix.width,
            height=matrix.height,
            created_at=int(time.mktime(datetime.timetuple(matrix.created_at))),
            index=content.index,
            columns=content.columns,
            data=content.data,
        )

    @staticmethod
    def _from_dto(dto: MatrixDTO) -> Tuple[Matrix, MatrixContent]:
        matrix = Matrix(
            id=dto.id,
            width=dto.width,
            height=dto.height,
            created_at=datetime.fromtimestamp(dto.created_at),
        )

        content = MatrixContent(
            data=dto.data, index=dto.index, columns=dto.columns
        )

        return matrix, content

    def create(self, data: List[List[MatrixData]]) -> str:
        matrix_hash = self.matrix_content_repository.save(data)
        with db():
            if not self.repo.get(matrix_hash):
                self.repo.save(
                    Matrix(
                        id=matrix_hash,
                        width=len(data[0] if len(data) > 0 else []),
                        height=len(data),
                        created_at=datetime.utcnow(),
                    )
                )
        return matrix_hash

    def create_by_importation(
        self, file: UploadFile, json: bool = False
    ) -> List[MatrixInfoDTO]:
        with file.file as f:
            if file.content_type == "application/zip":
                input_zip = ZipFile(BytesIO(f.read()))
                files = {
                    info.filename: input_zip.read(info.filename)
                    for info in input_zip.infolist()
                    if not info.is_dir()
                }
                matrix_info: List[MatrixInfoDTO] = []
                for name in files.keys():
                    if all(
                        [
                            not name.startswith("__MACOSX/"),
                            not name.startswith(".DS_Store"),
                        ]
                    ):
                        id = self.file_importation(files[name], json)
                        matrix_info.append(MatrixInfoDTO(id=id, name=name))
                return matrix_info
            else:
                id = self.file_importation(f.read(), json)
                return [MatrixInfoDTO(id=id, name=file.filename)]

    def file_importation(self, file: bytes, is_json: bool = False) -> str:
        if is_json:
            return self.create(MatrixContent.parse_raw(file).data)
        else:
            data = parse_tsv_matrix(file)
            return self.create(data)

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

        MatrixService.check_access_permission(
            dataset, params.user, raise_error=True
        )
        return dataset

    def create_dataset(
        self,
        dataset_info: MatrixDataSetUpdateDTO,
        matrices: List[MatrixInfoDTO],
        params: RequestParameters,
    ) -> MatrixDataSet:
        if not params.user:
            raise UserHasNotPermissionError()

        groups = [
            self.user_service.get_group(group_id, params)
            for group_id in dataset_info.groups
        ]
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
        MatrixService.check_access_permission(
            dataset, params.user, write=True, raise_error=True
        )
        groups = [
            self.user_service.get_group(group_id, params)
            for group_id in dataset_info.groups
        ]
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

        Args:
            dataset_name: the dataset name search query
            filter_own: indicate if only the current user datasets should be returned
            params: The request parameter containing user information

        Returns:
            the list of matching MatrixUserMetadata
        """
        user = params.user
        if not user:
            raise UserHasNotPermissionError()

        datasets = self.repo_dataset.query(
            dataset_name, user.impersonator if filter_own else None
        )
        return [
            dataset.to_dto()
            for dataset in datasets
            if dataset.public
            or user.is_or_impersonate(dataset.owner_id)
            or len(
                [
                    group
                    for group in dataset.groups
                    if group.id in [jwtgroup.id for jwtgroup in user.groups]
                ]
            )
            > 0
        ]

    def delete_dataset(self, id: str, params: RequestParameters) -> str:
        if not params.user:
            raise UserHasNotPermissionError()

        dataset = self.repo_dataset.get(id)

        if dataset is None:
            raise MatrixDataSetNotFound()

        MatrixService.check_access_permission(
            dataset, params.user, write=True, raise_error=True
        )
        self.repo_dataset.delete(id)
        return id

    def get(self, id: str) -> Optional[MatrixDTO]:
        matrix_content = self.matrix_content_repository.get(id)
        matrix = self.repo.get(id)

        if matrix_content and matrix:
            return MatrixService._to_dto(matrix, matrix_content)
        else:
            return None

    def exists(self, id: str) -> bool:
        return self.matrix_content_repository.exists(id) and self.repo.exists(
            id
        )

    def delete(self, id: str) -> None:
        self.matrix_content_repository.delete(id)
        self.repo.delete(id)

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
            dataset.owner_id == user.id
            or dataset.owner_id == user.impersonator
        ) or (
            any([group.id in dataset_groups for group in user.groups])
            and not write
        )
        if not access and raise_error:
            raise UserHasNotPermissionError()
        return access

    def create_matrix_files(
        self, dataset: MatrixDataSet, export_path: Path
    ) -> str:
        assert export_path.name.endswith(".zip")
        with tempfile.TemporaryDirectory(
            dir=self.config.storage.tmp_dir
        ) as tmpdir:
            stopwatch = StopWatch()
            for mtx_info in dataset.matrices:
                mtx = self.get(mtx_info.matrix.id)
                if not mtx:
                    continue
                write_tsv_matrix(mtx, tmpdir)
            filename = shutil.make_archive(
                base_name=os.path.splitext(export_path)[0],
                format="zip",
                root_dir=tmpdir,
            )
            stopwatch.log_elapsed(
                lambda x: logger.info(
                    f"Matrix dataset {dataset.id} exported (zipped mode) in {x}s"
                )
            )
        return filename if filename else ""

    def download_dataset(
        self,
        dataset_id: str,
        params: RequestParameters,
    ) -> FileDownloadTaskDTO:
        """
        Export study output to a zip file.
        Args:
            dataset_id: matrix dataset id
            params: request parameters
        """
        if not params.user:
            raise UserHasNotPermissionError()
        dataset = self.repo_dataset.get(dataset_id)
        if dataset is None:
            raise MatrixDataSetNotFound()
        MatrixService.check_access_permission(
            dataset, params.user, raise_error=True
        )

        logger.info(f"Exporting matrix dataset {dataset_id}")
        export_name = f"Exporting matrix dataset {dataset_id}"
        export_file_download = self.file_transfer_manager.request_download(
            f"matrixdataset-{dataset_id}.zip",
            export_name,
            params.user,
        )
        export_path = Path(export_file_download.path)
        export_id = export_file_download.id

        def export_task(notifier: TaskUpdateNotifier) -> TaskResult:
            try:
                matrix_dataset = self.repo_dataset.get(dataset_id)
                if matrix_dataset is None:
                    return TaskResult(
                        success=False,
                        message=f"Matrix dataset {dataset_id} not found",
                    )
                self.create_matrix_files(
                    dataset=matrix_dataset, export_path=export_path
                )
                self.file_transfer_manager.set_ready(export_id)
                return TaskResult(
                    success=True,
                    message=f"Matrix dataset {dataset_id} successfully exported",
                )
            except Exception as e:
                self.file_transfer_manager.fail(export_id, str(e))
                raise e

        task_id = self.task_service.add_task(
            export_task,
            export_name,
            task_type=TaskType.EXPORT,
            custom_event_messages=None,
            request_params=params,
        )

        return FileDownloadTaskDTO(
            file=export_file_download.to_dto(), task=task_id
        )

    def download_matrix(
        self,
        matrix_id: str,
        tmp_file: Path,
        params: RequestParameters,
    ) -> None:
        """
        Export study output to a zip file.
        Args:
            matrix_id: matrix id
            tmp_file: temporary file
            params: request parameters
        """
        if not params.user:
            raise UserHasNotPermissionError()
        matrix = self.get(matrix_id)
        if matrix:
            write_tsv_matrix_to_file(matrix, str(tmp_file))
