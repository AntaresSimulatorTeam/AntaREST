import time
from datetime import datetime
from typing import List, Optional, Tuple

from antarest.matrixstore.model import (
    MatrixDTO,
    MatrixFreq,
    Matrix,
    MatrixContent,
)
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
)


class MatrixService:
    def __init__(
        self, repo: MatrixRepository, content: MatrixContentRepository
    ):
        self.repo = repo
        self.repo_content = content

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
