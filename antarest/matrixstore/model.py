import enum
from typing import List, Any, Optional

from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
from sqlalchemy import Column, String, Enum, DateTime

from antarest.common.persistence import Base


class MatrixType(enum.IntEnum):
    INPUT = 1
    OUTPUT = 2


class MatrixFreq(enum.IntEnum):
    HOURLY = 1
    DAILY = 2
    WEEKLY = 3
    MONTHLY = 4
    ANNUAL = 5


class Matrix(Base):  # type: ignore
    __tablename__ = "matrix"

    id = Column(String(32), primary_key=True)
    type = Column(Enum(MatrixType))
    freq = Column(Enum(MatrixFreq))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)  # TODO useless since matrix is immutable ?

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Matrix):
            return False

        res: bool = (
            self.id == other.id
            and self.type == other.type
            and self.freq == other.freq
            and self.created_at == other.created_at
            and self.updated_at == other.updated_at
        )
        return res


@dataclass
class MatrixDTO(DataClassJsonMixin):  # type: ignore
    type: MatrixType
    freq: MatrixFreq
    index: List[str]
    columns: List[str]
    data: List[List[int]]
    created_at: int = 0
    updated_at: int = 0
    id: str = ""


@dataclass
class MatrixContent(DataClassJsonMixin):  # type: ignore
    data: List[List[int]]
    index: List[str]
    columns: List[str]
