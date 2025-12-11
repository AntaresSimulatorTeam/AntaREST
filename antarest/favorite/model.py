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
import logging

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.testing.schema import mapped_column

from antarest.core.persistence import Base

logger = logging.getLogger(__name__)


class Favorite(Base):
    """


    Attributes:
        user_id: the user's id
        study_id: the study's id that was put in favorites
    """

    __tablename__ = "favorite"

    user_id: Mapped[str] = mapped_column(String(255), nullable=False, primary_key=True)
    study_id: Mapped[str] = mapped_column(String(255), nullable=False, primary_key=True)
