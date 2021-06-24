import enum
from typing import List, Any

from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin  # type: ignore
from pydantic import BaseModel
from sqlalchemy import Column, String, Enum, DateTime  # type: ignore

from antarest.common.persistence import Base


class MatrixFreq(enum.IntEnum):
    HOURLY = 1
    DAILY = 2
    WEEKLY = 3
    MONTHLY = 4
    ANNUAL = 5

    @staticmethod
    def from_str(data: str) -> "MatrixFreq":
        if data == "hourly":
            return MatrixFreq.HOURLY
        elif data == "daily":
            return MatrixFreq.DAILY
        elif data == "weekly":
            return MatrixFreq.WEEKLY
        elif data == "monthly":
            return MatrixFreq.MONTHLY
        elif data == "annual":
            return MatrixFreq.ANNUAL
        raise NotImplementedError()


class Matrix(Base):  # type: ignore
    __tablename__ = "matrix"

    id = Column(String(32), primary_key=True)
    freq = Column(Enum(MatrixFreq))
    created_at = Column(DateTime)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Matrix):
            return False

        res: bool = (
            self.id == other.id
            and self.freq == other.freq
            and self.created_at == other.created_at
        )
        return res


class MatrixDTO(BaseModel):
    freq: MatrixFreq
    index: List[str]
    columns: List[str]
    data: List[List[int]]
    created_at: int = 0
    id: str = ""


@dataclass
class MatrixContent(DataClassJsonMixin):  # type: ignore
    data: List[List[int]]
    index: List[str]
    columns: List[str]
