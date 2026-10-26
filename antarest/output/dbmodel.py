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
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.persistence import Base


class Output(Base):
    """
    Metadata for one output.

    Attributes:
        study_id: ID of the study to which the output belongs.
        output_id: ID of the output.
        last_unarchiving_date: Last successful unarchiving date in naive UTC, if any.
        disk_space_bytes: Disk space used by the output, in bytes. Used as a cached value, should be invalidated
                          by setting it to None when the actual size changes (archival ...).
    """

    __tablename__ = "output"

    study_id: Mapped[str] = mapped_column(
        String(),
        ForeignKey("study.id", name="fk_output_study_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    output_id: Mapped[str] = mapped_column(String(), primary_key=True, nullable=False)
    last_unarchiving_date: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    disk_space_bytes: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
