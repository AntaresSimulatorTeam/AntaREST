import hashlib
import json
import logging
import os
from typing import Optional, List, Any

from sqlalchemy import exists

from antarest.common.config import Config
from antarest.common.custom_types import JSON
from antarest.common.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.model import Matrix, MatrixType, MatrixFreq


class MatrixRepository:
    """
    Database connector to manage Matrix entity.
    """

    def __init__(self) -> None:
        self.logger = logging.Logger(self.__class__.__name__)

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

    def get_by_type_freq(
        self,
        type: Optional[MatrixType] = None,
        freq: Optional[MatrixFreq] = None,
    ) -> List[Matrix]:
        matrix: List[Matrix] = (
            db.session.query(Matrix)
            .filter((Matrix.type == type) | (Matrix.freq == freq))
            .all()
        )
        return matrix

    def delete(self, id: str) -> None:
        g = db.session.query(Matrix).get(id)
        db.session.delete(g)
        db.session.commit()

        self.logger.debug(f"Matrix {id} deleted")


class MatrixContentRepository:
    ITEMS = ["columns", "index", "data"]

    def __init__(self, config: Config) -> None:
        self.bucket = config.matrixstore.bucket

    @staticmethod
    def _compute_hash(data: str) -> str:
        return hashlib.md5(data.encode()).hexdigest()

    def get(self, id: str) -> Optional[JSON]:
        file = self.bucket / id
        return json.load(open(file)) if file.exists() else None

    def save(self, data: JSON) -> str:
        data = {i: data[i] for i in MatrixContentRepository.ITEMS}
        stringify = json.dumps(data)
        h = MatrixContentRepository._compute_hash(stringify)
        (self.bucket / h).write_text(stringify)

        return h

    def delete(self, id: str) -> None:
        file = self.bucket / id
        if file.exists():
            os.remove(file)
