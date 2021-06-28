import enum
from typing import List, Any

from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin  # type: ignore
from pydantic import BaseModel
from sqlalchemy import Column, String, Enum, DateTime, Table, ForeignKey, Integer  # type: ignore
from sqlalchemy.orm import relationship

from antarest.common.persistence import Base
from antarest.login.model import Identity


class MatrixFreq(enum.IntEnum):
    HOURLY = 1
    DAILY = 2
    WEEKLY = 3
    MONTHLY = 4
    ANNUAL = 5


groups_matrix_metadata = Table(
    "matrix_group",
    Base.metadata,
    Column("matrix_id", String(64), ForeignKey("matrix.id"), primary_key=True),
    Column("owner_id", Integer(), ForeignKey("identities.id"), primary_key=True),
    Column("group_id", String(36), ForeignKey("groups.id"), primary_key=True),
)


class Matrix(Base):  # type: ignore
    __tablename__ = "matrix"

    id = Column(String(64), primary_key=True)
    freq = Column(Enum(MatrixFreq))
    created_at = Column(DateTime)
    users_metadata = relationship("MatrixMetadataOwnership")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Matrix):
            return False

        res: bool = (
                self.id == other.id
                and self.freq == other.freq
                and self.created_at == other.created_at
        )
        return res


MATRIX_METADATA_PUBLIC_MODE = "is_public"

class MatrixMetadataOwnership(Base):
    __tablename__ = "matrix_metadata_ownership"

    matrix_id = Column(String(64), ForeignKey(Matrix.id), primary_key=True)
    owner_id = Column(Integer, ForeignKey(Identity.id), primary_key=True)

    matrix = relationship(Matrix, foreign_keys='MatrixMetadataOwnership.matrix_id', back_populates="users_metadata")
    owner = relationship(Identity)
    groups = relationship(
        "Group", secondary=lambda: groups_matrix_metadata,
        primaryjoin="and_(MatrixMetadataOwnership.matrix_id==matrix_group.c.matrix_id, MatrixMetadataOwnership.owner_id==matrix_group.c.owner_id)"
    )
    metadata_ = relationship("MatrixMetadata", primaryjoin="and_(MatrixMetadataOwnership.matrix_id==foreign(MatrixMetadata.matrix_id), MatrixMetadataOwnership.owner_id==foreign(MatrixMetadata.owner_id))")


class MatrixMetadata(Base):
    __tablename__ = "matrix_metadata"

    matrix_id = Column(String(64), ForeignKey(Matrix.id), primary_key=True)
    owner_id = Column(Integer, ForeignKey(Identity.id), primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String)


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
