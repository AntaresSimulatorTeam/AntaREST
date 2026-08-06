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
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.persistence import Base


class Output(Base):
    __tablename__ = "output"

    study_id: Mapped[str] = mapped_column(
        String(),
        ForeignKey("study.id", name="fk_output_study_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    output_id: Mapped[str] = mapped_column(String(), primary_key=True, nullable=False)
    disk_space_bytes: Mapped[int] = mapped_column(BigInteger(), nullable=False)
