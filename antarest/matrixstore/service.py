import time
import csv
from datetime import datetime
from http import HTTPStatus
from typing import List, Optional, Tuple, Dict, Any

from fastapi import HTTPException

from antarest.common.jwt import JWTUser
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.login.model import Group, GroupDTO
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
)
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
    MatrixDataSetRepository,
)


class MatrixService:
    def __init__(
        self,
        repo: MatrixRepository,
        repo_dataset: MatrixDataSetRepository,
        content: MatrixContentRepository,
        user_service: LoginService,
    ):
        self.repo = repo
        self.repo_dataset = repo_dataset
        self.repo_content = content
        self.user_service = user_service

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

    def create(self, data: MatrixDTO) -> str:
        matrix, content = MatrixService._from_dto(data)
        matrix.created_at = datetime.now()
        matrix.id = self.repo_content.save(content)
        self.repo.save(matrix)

        return matrix.id

    def create_by_importation(self, file: bytes) -> str:
        str_file = str(file, "UTF-8")
        reader = csv.reader(str_file.split("\n"), delimiter="\t")
        data = []
        columns: List[int] = []
        for row in reader:
            if row:
                print("ROW: ", row)
                data.append([int(elm) for elm in row])
            if len(columns) == 0:
                columns = list(range(0, len(row)))

        matrix = MatrixDTO(
            width=len(columns),
            height=len(data),
            index=[],
            columns=columns,
            data=data,
        )
        print("WIDTH: ", matrix.width, "; HEIGHT: ", matrix.height)
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
            created_at=datetime.now(),
            updated_at=datetime.now(),
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
            updated_at=datetime.now(),
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

    def delete_dataset(self, id: str) -> None:
        self.repo_dataset.delete(id)

    def get(self, id: str) -> Optional[MatrixDTO]:
        data = self.repo_content.get(id)
        matrix = self.repo.get(id)

        if data and matrix:
            return MatrixService._to_dto(matrix, data)
        else:
            return None

    def delete(self, id: str) -> None:
        self.repo_content.delete(id)
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
