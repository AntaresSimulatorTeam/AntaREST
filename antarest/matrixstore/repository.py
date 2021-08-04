import hashlib
import json
import logging
from typing import List, Optional

from sqlalchemy import exists, and_  # type: ignore
from sqlalchemy.orm import aliased  # type: ignore

from antarest.core.config import Config
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.model import (
    Matrix,
    MatrixContent,
    MatrixDataSet,
)


class MatrixDataSetRepository:
    """
    Database connector to manage Matrix metadata entity
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def save(self, matrix_user_metadata: MatrixDataSet) -> MatrixDataSet:
        res = db.session.query(
            exists().where(MatrixDataSet.id == matrix_user_metadata.id)
        ).scalar()
        if res:
            matrix_user_metadata = db.session.merge(matrix_user_metadata)
        else:
            db.session.add(matrix_user_metadata)
        db.session.commit()

        self.logger.debug(
            f"Matrix dataset {matrix_user_metadata.id} for user {matrix_user_metadata.owner_id} saved"
        )
        return matrix_user_metadata

    def get(self, id: str) -> Optional[MatrixDataSet]:
        matrix: MatrixDataSet = db.session.query(MatrixDataSet).get(id)
        return matrix

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

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def save(self, matrix: Matrix) -> Matrix:
        res = db.session.query(exists().where(Matrix.id == matrix.id)).scalar()
        if res:
            db.session.merge(matrix)
        else:
            db.session.add(matrix)
        db.session.commit()

        self.logger.debug(f"Matrix {matrix.id} saved")
        return matrix

    def get(self, id: str) -> Optional[Matrix]:
        matrix: Matrix = db.session.query(Matrix).get(id)
        return matrix

    def exists(self, id: str) -> bool:
        res: bool = db.session.query(exists().where(Matrix.id == id)).scalar()
        return res

    def delete(self, id: str) -> None:
        g = db.session.query(Matrix).get(id)
        db.session.delete(g)
        db.session.commit()

        self.logger.debug(f"Matrix {id} deleted")


class MatrixContentRepository:
    def __init__(self, config: Config) -> None:
        self.bucket = config.storage.matrixstore
        self.bucket.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _compute_hash(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def get(self, id: str) -> Optional[MatrixContent]:
        file = self.bucket / id
        if not file.exists():
            return None

        data = json.load(open(file))
        return MatrixContent.from_dict(data)  # type: ignore

    def save(self, content: MatrixContent) -> str:
        stringify = content.to_json()
        h = MatrixContentRepository._compute_hash(stringify)
        (self.bucket / h).write_text(stringify)

        return h

    def delete(self, id: str) -> None:
        file = self.bucket / id
        if file.exists():
            file.unlink()
