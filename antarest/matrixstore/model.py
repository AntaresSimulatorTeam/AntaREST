import enum
from distutils.util import strtobool
from typing import List, Any, Dict, Optional

from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin  # type: ignore
from pydantic import BaseModel
from sqlalchemy import Column, String, Enum, DateTime, Table, ForeignKey, Integer  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore
from sqlalchemy.orm.collections import attribute_mapped_collection  # type: ignore

from antarest.common.persistence import Base
from antarest.login.model import Identity, Group, GroupDTO
from antarest.matrixstore.exceptions import MetadataKeyNotAllowed


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


groups_matrix_metadata = Table(
    "matrix_group",
    Base.metadata,
    Column("matrix_id", String(64), ForeignKey("matrix.id"), primary_key=True),
    Column(
        "owner_id", Integer(), ForeignKey("identities.id"), primary_key=True
    ),
    Column("group_id", String(36), ForeignKey("groups.id"), primary_key=True),
)


class Matrix(Base):  # type: ignore
    __tablename__ = "matrix"

    id = Column(String(64), primary_key=True)
    freq = Column(Enum(MatrixFreq))
    created_at = Column(DateTime)
    users_metadata = relationship("MatrixUserMetadata")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Matrix):
            return False

        res: bool = (
            self.id == other.id
            and self.freq == other.freq
            and self.created_at == other.created_at
        )
        return res


class MatrixMetadataDTO(BaseModel):
    id: str
    name: Optional[str] = None
    metadata: Dict[str, str] = {}
    public: bool = True
    groups: List[GroupDTO] = []


MATRIX_METADATA_PUBLIC_MODE = "is_public"
MATRIX_METADATA_NAME = "name"
MATRIX_METADATA_RESERVED_KEYS = [
    MATRIX_METADATA_NAME,
    MATRIX_METADATA_PUBLIC_MODE,
]


class MatrixUserMetadata(Base):  # type: ignore
    __tablename__ = "matrix_user_metadata"

    matrix_id = Column(
        String(64),
        ForeignKey(
            "matrix.id",
            name="fk_matrix_user_metadata_matrix_id",
            deferrable=False,
        ),
        primary_key=True,
    )
    owner_id = Column(
        Integer,
        ForeignKey(
            "identities.id",
            name="fk_matrix_user_metadata_identities_id",
            deferrable=False,
        ),
        primary_key=True,
    )

    matrix = relationship(
        Matrix,
        foreign_keys="MatrixUserMetadata.matrix_id",
        back_populates="users_metadata",
    )
    owner = relationship(Identity)
    groups = relationship(
        "Group",
        secondary=lambda: groups_matrix_metadata,
        primaryjoin="and_(MatrixUserMetadata.matrix_id==matrix_group.c.matrix_id, MatrixUserMetadata.owner_id==matrix_group.c.owner_id)",
    )
    metadata_ = relationship(
        "MatrixMetadata",
        primaryjoin="and_(MatrixUserMetadata.matrix_id==foreign(MatrixMetadata.matrix_id), MatrixUserMetadata.owner_id==foreign(MatrixMetadata.owner_id))",
        collection_class=attribute_mapped_collection("key"),
        cascade="all, delete-orphan",
    )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MatrixUserMetadata):
            return False

        res: bool = (
            self.matrix_id == other.matrix_id
            and self.owner_id == other.owner_id
            and self.groups == other.groups
            and self.metadata_ == other.metadata_
        )
        return res

    def is_public(self) -> bool:
        return MATRIX_METADATA_PUBLIC_MODE in self.metadata_.keys() and bool(
            strtobool(self.metadata_[MATRIX_METADATA_PUBLIC_MODE].value)
        )

    def get_name(self) -> Optional[str]:
        if MATRIX_METADATA_NAME in self.metadata_.keys():
            return str(self.metadata_[MATRIX_METADATA_NAME].value)
        return None

    def to_dto(self) -> MatrixMetadataDTO:
        return MatrixMetadataDTO(
            id=self.matrix_id,
            name=self.get_name(),
            groups=[
                GroupDTO(id=group.id, name=group.name) for group in self.groups
            ],
            public=self.is_public(),
            metadata=MatrixUserMetadata.strip_metadata_reserved_keys(
                {
                    key: self.metadata_[key].value
                    for key in self.metadata_.keys()
                }
            ),
        )

    @staticmethod
    def strip_metadata_reserved_keys(
        metadata: Dict[str, str], raise_exception: bool = False
    ) -> Dict[str, Any]:
        stripped = {
            key: metadata[key]
            for key in metadata.keys()
            if key not in MATRIX_METADATA_RESERVED_KEYS
        }
        if raise_exception and len(stripped.keys()) != len(metadata.keys()):
            raise MetadataKeyNotAllowed(
                f"Cannot use reserved key {MATRIX_METADATA_RESERVED_KEYS}"
            )
        return stripped


class MatrixMetadata(Base):  # type: ignore
    __tablename__ = "matrix_metadata"

    matrix_id = Column(String(64), ForeignKey("matrix.id"), primary_key=True)
    owner_id = Column(Integer, ForeignKey("identities.id"), primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MatrixMetadata):
            return False

        res: bool = (
            self.matrix_id == other.matrix_id
            and self.owner_id == other.owner_id
            and self.key == other.key
            and self.value == other.value
        )
        return res


class MatrixUserMetadataQuery(BaseModel):
    name: Optional[str]
    metadata: Dict[str, str] = {}
    owner: Optional[int]


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
