# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import datetime
import uuid
from typing import Any, List, TypeAlias

from pydantic import field_serializer
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing_extensions import override

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel
from antarest.login.model import Group, GroupDTO, Identity, UserInfo


class Matrix(Base):  # type: ignore
    """
    Represents a matrix object in the database.

    Attributes:
        id: A SHA256 hash for the matrix data (primary key).
        width: Number of columns in the matrix.
        height: Number of rows in the matrix.
        created_at: Creation date of the matrix (unknown usage).
    """

    # noinspection SpellCheckingInspection
    __tablename__ = "matrix"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime)
    version: Mapped[int] = mapped_column(Integer)

    @override
    def __repr__(self) -> str:  # pragma: no cover
        """Returns a string representation of the matrix."""
        return f"Matrix(id={self.id}, shape={(self.height, self.width)}, created_at={self.created_at})"

    @override
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


class MatrixInfoDTO(AntaresBaseModel):
    id: str
    name: str


class MatrixDataSetDTO(AntaresBaseModel):
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
    Column("dataset_id", String(64), ForeignKey("dataset.id"), primary_key=True),
    Column("group_id", String(36), ForeignKey("groups.id"), primary_key=True),
)


class MatrixMetadataDTO(AntaresBaseModel, extra="forbid", populate_by_name=True):
    id: str
    width: int
    height: int
    created_at: datetime.datetime
    version: int

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime.datetime) -> str:
        return created_at.strftime("%Y-%m-%d %H:%M:%S.%f")


class MatrixDataSetRelation(Base):  # type: ignore
    # noinspection SpellCheckingInspection
    __tablename__ = "dataset_matrices"

    # noinspection SpellCheckingInspection
    dataset_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("dataset.id", name="fk_matrixdatasetrelation_dataset_id"),
        primary_key=True,
    )
    # noinspection SpellCheckingInspection
    matrix_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("matrix.id", name="fk_matrixdatasetrelation_matrix_id"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String, primary_key=True)
    matrix: Mapped[Matrix] = relationship(Matrix)

    @override
    def __repr__(self) -> str:  # pragma: no cover
        """Returns a string representation of the matrix."""
        return f"MatrixDataSetRelation(dataset_id={self.dataset_id}, matrix_id={self.matrix_id}, name={self.name})"

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MatrixDataSetRelation):
            return False

        res: bool = (
            self.matrix_id == other.matrix_id and self.dataset_id == other.dataset_id and self.name == other.name
        )

        return res


class MatrixDataSet(Base):  # type: ignore
    """
    Represents a user dataset containing matrices in the database.

    Attributes:
        id: The unique identifier of the dataset (primary key).
        name: The name of the dataset.
        owner_id: The foreign key referencing the owner's identity.
        public: Indicates whether the dataset is public or not.
        created_at: The creation date of the dataset.
        updated_at: The last update date of the dataset.

    Relationships:
        owner (Identity): The relationship to the owner's identity.
        groups (List[Group]): The relationship to groups associated with the dataset.
        matrices (List[MatrixDataSetRelation]): The relationship to matrix dataset relations.
    """

    # noinspection SpellCheckingInspection
    __tablename__ = "dataset"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name: Mapped[str] = mapped_column(String)
    # noinspection SpellCheckingInspection
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("identities.id", name="fk_matrixdataset_identities_id"),
    )
    public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime)

    owner: Mapped[Identity] = relationship(Identity)
    groups: Mapped[List[Group]] = relationship(
        "Group",
        secondary=lambda: groups_dataset_relation,
    )
    matrices = relationship(MatrixDataSetRelation, cascade="all, delete, delete-orphan")

    def to_dto(self) -> MatrixDataSetDTO:
        return MatrixDataSetDTO(
            id=self.id,
            name=self.name,
            matrices=[MatrixInfoDTO(name=matrix.name, id=matrix.matrix.id) for matrix in self.matrices],
            owner=UserInfo(id=self.owner.id, name=self.owner.name),
            groups=[GroupDTO(id=group.id, name=group.name) for group in self.groups],
            public=self.public,
            created_at=str(self.created_at),
            updated_at=str(self.updated_at),
        )

    @override
    def __repr__(self) -> str:  # pragma: no cover
        """Returns a string representation of the matrix."""
        return (
            f"MatrixDataSet(id={self.id},"
            f" name={self.name},"
            f" owner_id={self.owner_id},"
            f" public={self.public},"
            f" created_at={self.created_at},"
            f" updated_at={self.updated_at})"
        )

    @override
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
# Reverting to only float because Any cause problem retrieving data from a node
# will have pandas forcing all to float anyway...
# this cause matrix dump on disk (and then hash id) to be different for basically the same matrices
MatrixData: TypeAlias = float


class MatrixDataSetUpdateDTO(AntaresBaseModel):
    name: str
    groups: List[str]
    public: bool
