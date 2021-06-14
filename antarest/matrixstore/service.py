from typing import List

from antarest.matrixstore.model import MatrixDTO, MatrixFreq, MatrixType
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
)


class MatrixService:
    def __init__(
        self, repo: MatrixRepository, content: MatrixContentRepository
    ):
        self.repo = repo
        self.content = content

    def save(self, data: MatrixDTO) -> str:
        pass

    def get(self, id: str) -> MatrixDTO:
        pass

    def get_by_type_freq(
        self, freq: MatrixFreq, type: MatrixType
    ) -> List[MatrixDTO]:
        pass

    def delete(self, id: str) -> None:
        pass
