import time
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

from fastapi import HTTPException

from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.login.model import Group
from antarest.login.service import LoginService
from antarest.matrixstore.model import (
    MatrixDTO,
    MatrixFreq,
    Matrix,
    MatrixContent,
    MatrixUserMetadata,
    MatrixMetadata,
    MATRIX_METADATA_PUBLIC_MODE,
    MatrixUserMetadataQuery,
    MATRIX_METADATA_NAME,
    MatrixMetadataDTO,
    MATRIX_METADATA_RESERVED_KEYS,
)
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
    MatrixMetadataRepository,
)


class MatrixService:
    def __init__(
        self,
        repo: MatrixRepository,
        repo_meta: MatrixMetadataRepository,
        content: MatrixContentRepository,
        user_service: LoginService,
    ):
        self.repo = repo
        self.repo_meta = repo_meta
        self.repo_content = content
        self.user_service = user_service

    @staticmethod
    def _to_dto(matrix: Matrix, content: MatrixContent) -> MatrixDTO:
        return MatrixDTO(
            id=matrix.id,
            freq=matrix.freq,
            created_at=int(time.mktime(datetime.timetuple(matrix.created_at))),
            index=content.index,
            columns=content.columns,
            data=content.data,
        )

    @staticmethod
    def _from_dto(dto: MatrixDTO) -> Tuple[Matrix, MatrixContent]:
        matrix = Matrix(
            id=dto.id,
            freq=dto.freq,
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

    def update_metadata(
        self,
        matrix_id: str,
        user_id: int,
        metadata: Dict[str, str],
        params: RequestParameters,
    ) -> MatrixUserMetadata:
        if not params.user or not params.user.is_or_impersonate(user_id):
            raise UserHasNotPermissionError()
        valid_metadata = self._strip_metadata_reserved_keys(metadata)
        user_meta = MatrixUserMetadata(
            matrix_id=matrix_id,
            owner_id=user_id,
            metadata_={
                key: MatrixMetadata(
                    matrix_id=matrix_id,
                    owner_id=user_id,
                    key=key,
                    value=valid_metadata[key],
                )
                for key in valid_metadata.keys()
            },
        )
        return self.repo_meta.save(user_meta)

    def update_group(
        self,
        matrix_id: str,
        user_id: int,
        group_ids: List[str],
        params: RequestParameters,
    ) -> MatrixUserMetadata:
        if not params.user or not params.user.is_or_impersonate(user_id):
            raise UserHasNotPermissionError()

        groups = [
            self.user_service.get_group(group_id, params)
            for group_id in group_ids
        ]
        user_meta = MatrixUserMetadata(
            matrix_id=matrix_id,
            owner_id=user_id,
            groups=groups,
        )
        return self.repo_meta.save(user_meta)

    def _patch_metadata(
        self,
        matrix_id: str,
        user_id: int,
        key: str,
        value: str,
        params: RequestParameters,
    ) -> MatrixUserMetadata:
        if not params.user or not params.user.is_or_impersonate(user_id):
            raise UserHasNotPermissionError()

        user_meta = self.repo_meta.get(matrix_id, user_id)
        if not user_meta:
            raise HTTPException(status_code=404)

        new_meta = user_meta.metadata_
        new_meta[key] = value
        user_meta = MatrixUserMetadata(
            matrix_id=matrix_id,
            owner_id=user_id,
            metadata_=new_meta,
        )
        return self.repo_meta.save(user_meta)

    def set_name(
        self,
        matrix_id: str,
        user_id: int,
        name: str,
        params: RequestParameters,
    ) -> MatrixUserMetadata:
        return self._patch_metadata(
            matrix_id, user_id, MATRIX_METADATA_NAME, name, params
        )

    def set_public(
        self,
        matrix_id: str,
        user_id: int,
        public_status: bool,
        params: RequestParameters,
    ) -> MatrixUserMetadata:
        return self._patch_metadata(
            matrix_id,
            user_id,
            MATRIX_METADATA_PUBLIC_MODE,
            str(public_status),
            params,
        )

    def list(
        self, query: MatrixUserMetadataQuery, params: RequestParameters
    ) -> List[MatrixMetadataDTO]:
        """
        List matrix user metadata

        Args:
            query: the metadata search query
            params: The request parameter containing user information

        Returns:
            the list of matching MatrixUserMetadata
        """
        user = params.user
        if not user:
            raise UserHasNotPermissionError()

        users_metadata = self.repo_meta.query(
            query.name, query.metadata, query.owner
        )
        return [
            MatrixMetadataDTO(
                id=metadata.matrix_id,
                name=metadata.metadata_.get("name", None),
                groups=[group for group in metadata.groups],
                public=metadata.is_public(),
                metadata=self._strip_metadata_reserved_keys(
                    metadata.metadata_
                ),
            )
            for metadata in users_metadata
            if metadata.is_public()
            or len(
                [group for group in metadata.groups if group.id in user.groups]
            )
            > 0
        ]

    def _strip_metadata_reserved_keys(
        self, metadata: Dict[str, Any], raise_exception: bool = False
    ) -> Dict[str, Any]:
        stripped = {
            key: metadata[key]
            for key in metadata.keys()
            if key not in MATRIX_METADATA_RESERVED_KEYS
        }
        if raise_exception and len(stripped.keys()) != len(metadata.keys()):
            raise Exception(
                f"Cannot use reserved key {MATRIX_METADATA_RESERVED_KEYS}"
            )
        return stripped

    def get(self, id: str) -> Optional[MatrixDTO]:
        data = self.repo_content.get(id)
        matrix = self.repo.get(id)

        if data and matrix:
            return MatrixService._to_dto(matrix, data)
        else:
            return None

    def get_by_freq(
        self,
        freq: Optional[MatrixFreq] = None,
    ) -> List[MatrixDTO]:
        matrices = self.repo.get_by_freq(freq)
        contents = [self.repo_content.get(m.id) for m in matrices]
        return [
            MatrixService._to_dto(m, c)
            for m, c in zip(matrices, contents)
            if c
        ]

    def delete(self, id: str) -> None:
        self.repo_content.delete(id)
        self.repo.delete(id)
