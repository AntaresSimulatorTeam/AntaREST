import uuid
from datetime import datetime
from typing import Any, List, Optional, Union

from pydantic import BaseModel
from sqlalchemy import Column, String, Enum, DateTime, Table, ForeignKey, Integer, Boolean  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore
from sqlalchemy.orm.collections import attribute_mapped_collection  # type: ignore

from antarest.core.persistence import Base
from antarest.login.model import GroupDTO, Identity, UserInfo


class Matrix(Base):  # type: ignore
    __tablename__ = "matrix"

    id = Column(String(64), primary_key=True)
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Matrix):
            return False

        res: bool = (
            self.id == other.id
            and self.width == other.width
            and self.height == other.height
            and self.created_at == other.created_at
        )
        return res


class MatrixInfoDTO(BaseModel):
    id: str
    name: str


class MatrixDataSetDTO(BaseModel):
    id: str
    name: str
    matrices: List[MatrixInfoDTO]
    owner: UserInfo
    groups: List[GroupDTO]
    public: bool
    created_at: str
    updated_at: str


groups_dataset_relation = Table(
    "matrix_dataset_group",
    Base.metadata,
    Column(
        "dataset_id", String(64), ForeignKey("dataset.id"), primary_key=True
    ),
    Column("group_id", String(36), ForeignKey("groups.id"), primary_key=True),
)


class MatrixDataSetRelation(Base):  # type: ignore
    __tablename__ = "dataset_matrices"
    dataset_id = Column(
        String,
        ForeignKey("dataset.id", name="fk_matrixdatasetrelation_dataset_id"),
        primary_key=True,
    )
    matrix_id = Column(
        String,
        ForeignKey("matrix.id", name="fk_matrixdatasetrelation_matrix_id"),
        primary_key=True,
    )
    name = Column(String, primary_key=True)
    matrix = relationship(Matrix)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MatrixDataSetRelation):
            return False

        res: bool = (
            self.matrix_id == other.matrix_id
            and self.dataset_id == other.dataset_id
            and self.name == other.name
        )

        return res


class MatrixDataSet(Base):  # type: ignore
    __tablename__ = "dataset"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name = Column(String)
    owner_id = Column(
        Integer,
        ForeignKey("identities.id", name="fk_matrixdataset_identities_id"),
    )
    public = Column(Boolean, default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    owner = relationship(Identity)
    groups = relationship(
        "Group",
        secondary=lambda: groups_dataset_relation,
    )
    matrices = relationship(
        MatrixDataSetRelation, cascade="all, delete, delete-orphan"
    )

    def to_dto(self) -> MatrixDataSetDTO:
        return MatrixDataSetDTO(
            id=self.id,
            name=self.name,
            matrices=[
                MatrixInfoDTO(name=matrix.name, id=matrix.matrix.id)
                for matrix in self.matrices
            ],
            owner=UserInfo(id=self.owner.id, name=self.owner.name),
            groups=[
                GroupDTO(id=group.id, name=group.name) for group in self.groups
            ],
            public=self.public,
            created_at=str(self.created_at),
            updated_at=str(self.updated_at),
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MatrixDataSet):
            return False

        res: bool = (
            self.id == other.id
            and self.name == other.name
            and self.public == other.public
            and self.matrices == other.matrices
            and self.groups == other.groups
            and self.owner_id == other.owner_id
        )

        return res


# TODO should be Union[float, int] but Any for now because of following issues
# https://github.com/samuelcolvin/pydantic/issues/1423
# https://github.com/samuelcolvin/pydantic/issues/1599
# https://github.com/samuelcolvin/pydantic/issues/1930
# TODO maybe we should reverting to only float because Any cause problem retrieving data from a node will have pandas forcing all to float anyway...
# this cause matrix dump on disk (and then hash id) to be different for basically the same matrices
MatrixData = float


class MatrixDTO(BaseModel):
    width: int
    height: int
    index: List[str]
    columns: List[str]
    data: List[List[MatrixData]]
    created_at: int = 0
    id: str = ""


class MatrixContent(BaseModel):
    data: List[List[MatrixData]]
    index: Optional[List[Union[int, str]]]
    columns: Optional[List[Union[int, str]]]


class MatrixDataSetUpdateDTO(BaseModel):
    name: str
    groups: List[str]
    public: bool
