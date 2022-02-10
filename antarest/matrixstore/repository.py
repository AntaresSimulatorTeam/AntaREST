import csv
import hashlib
import json
import logging
from typing import List, Optional, cast

from sqlalchemy import exists, and_  # type: ignore
from sqlalchemy.orm import aliased  # type: ignore

from antarest.core.config import Config
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.model import (
    Matrix,
    MatrixContent,
    MatrixDataSet,
    MatrixData,
)

logger = logging.getLogger(__name__)


class MatrixDataSetRepository:
    """
    Database connector to manage Matrix metadata entity
    """

    def save(self, matrix_user_metadata: MatrixDataSet) -> MatrixDataSet:
        res = db.session.query(
            exists().where(MatrixDataSet.id == matrix_user_metadata.id)
        ).scalar()
        if res:
            matrix_user_metadata = db.session.merge(matrix_user_metadata)
        else:
            db.session.add(matrix_user_metadata)
        db.session.commit()

        logger.debug(
            f"Matrix dataset {matrix_user_metadata.id} for user {matrix_user_metadata.owner_id} saved"
        )
        return matrix_user_metadata

    def get(self, id: str) -> Optional[MatrixDataSet]:
        matrix: MatrixDataSet = db.session.query(MatrixDataSet).get(id)
        return matrix

    def get_all_datasets(self) -> List[MatrixDataSet]:
        matrix_datasets: List[MatrixDataSet] = db.session.query(
            MatrixDataSet
        ).all()
        return matrix_datasets

    def query(
        self,
        name: Optional[str],
        owner: Optional[int] = None,
    ) -> List[MatrixDataSet]:
        """
        Query a list of MatrixUserMetadata by searching for each one separatly if a set of filter match
        Args:
            name: the partial name of dataset
            owner: owner id to filter the result with

        Returns:
            the list of metadata per user, matching the query
        """
        query = db.session.query(MatrixDataSet)
        if name is not None:
            query = query.filter(MatrixDataSet.name.ilike(f"%{name}%"))
        if owner is not None:
            query = query.filter(MatrixDataSet.owner_id == owner)
        datasets: List[MatrixDataSet] = query.distinct().all()
        return datasets

    def delete(self, dataset_id: str) -> None:
        dataset = db.session.query(MatrixDataSet).get(dataset_id)
        db.session.delete(dataset)
        db.session.commit()


class MatrixRepository:
    """
    Database connector to manage Matrix entity.
    """

    def save(self, matrix: Matrix) -> Matrix:
        res = db.session.query(exists().where(Matrix.id == matrix.id)).scalar()
        if res:
            db.session.merge(matrix)
        else:
            db.session.add(matrix)
        db.session.commit()

        logger.debug(f"Matrix {matrix.id} saved")
        return matrix

    def get(self, id: str) -> Optional[Matrix]:
        matrix: Matrix = db.session.query(Matrix).get(id)
        return matrix

    def exists(self, id: str) -> bool:
        res: bool = db.session.query(exists().where(Matrix.id == id)).scalar()
        return res

    def delete(self, id: str) -> None:
        g = db.session.query(Matrix).get(id)
        if g:
            db.session.delete(g)
            db.session.commit()
        else:
            logger.warning(
                f"Trying to delete matrix {id}, but was not found in database!"
            )
        logger.debug(f"Matrix {id} deleted")


class MatrixContentRepository:
    def __init__(self, config: Config) -> None:
        self.bucket = config.storage.matrixstore
        self.bucket.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def initialize_matrix_content(matrix_content: MatrixContent) -> None:
        if matrix_content.index is None:
            matrix_content.index = list(range(0, len(matrix_content.data)))
        else:
            assert len(matrix_content.index) == len(matrix_content.data)
        if matrix_content.columns is None:
            if len(matrix_content.data) > 0:
                matrix_content.columns = list(
                    range(0, len(matrix_content.data[0]))
                )
            else:
                matrix_content.columns = []
        else:
            if len(matrix_content.data) > 0:
                assert len(matrix_content.columns) == len(
                    matrix_content.data[0]
                )
            else:
                assert len(matrix_content.columns) == 0

    @staticmethod
    def _compute_hash(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def _write_matrix_data(self, h: str, data: List[List[MatrixData]]) -> None:
        file_path = self.bucket / f"{h}.tsv"
        with open(file_path, "w", newline="") as fd:
            tsv_output = csv.writer(fd, delimiter="\t")
            tsv_output.writerows(data)

    def get(self, id: str) -> Optional[MatrixContent]:
        file = self.bucket / f"{id}.tsv"
        if not file.exists():
            return None

        tsv_data = csv.reader(open(file, newline=""), delimiter="\t")
        data = [[MatrixData(s) for s in l] for l in list(tsv_data)]
        matrix_content = MatrixContent(data=data)
        self.initialize_matrix_content(matrix_content)

        return matrix_content

    def exists(self, id: str) -> bool:
        file = self.bucket / f"{id}.tsv"
        return file.exists()

    def save(self, content: List[List[MatrixData]]) -> str:
        stringify = json.dumps(content)
        h = MatrixContentRepository._compute_hash(stringify)

        if not (self.bucket / f"{h}.tsv").exists():
            self._write_matrix_data(h, content)
        return h

    def delete(self, id: str) -> None:
        matrix_file = self.bucket / f"{id}.tsv"
        if matrix_file.exists():
            matrix_file.unlink()
