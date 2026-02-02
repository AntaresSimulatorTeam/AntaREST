# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import logging

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel
from antarest.study.model import Directory, Study

logger = logging.getLogger(__name__)


class FavoriteStudyDTO(AntaresBaseModel, extra="forbid"):
    study_id: str
    study_name: str


class FavoriteStudy(Base):
    """


    Attributes:
        user_id: the user's id
        study_id: the study's id that was put in favorites
    """

    __tablename__ = "favorite_study"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("identities.id", name="fk_user_id_favorite_study", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    study_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("study.id", name="fk_study_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    study: Mapped["Study"] = relationship(Study)

    def to_dto(self) -> FavoriteStudyDTO:
        return FavoriteStudyDTO(study_id=self.study_id, study_name=self.study.name)


class FavoriteDirectoryDTO(AntaresBaseModel, extra="forbid"):
    directory_id: str
    directory_name: str


class FavoriteDirectory(Base):
    __tablename__ = "favorite_directory"

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        primary_key=True,
    )
    directory_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("directory.id", name="fk_directory_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    directory: Mapped["Directory"] = relationship(Directory)

    def to_dto(self) -> FavoriteDirectoryDTO:
        return FavoriteDirectoryDTO(directory_id=self.directory_id, directory_name=self.directory.name)
