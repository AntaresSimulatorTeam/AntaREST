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

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel
from antarest.study.model import Study

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

    user_id: Mapped[str] = mapped_column(
        String(255),
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
