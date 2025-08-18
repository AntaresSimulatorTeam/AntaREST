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

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from antarest.core.persistence import Base
from antarest.study.business.model.link_model import (
    AssetType,
    LinkStyle,
    TransmissionCapacity,
)

if TYPE_CHECKING:
    from antarest.study.model import Study


class Link(Base):
    __tablename__ = "link"

    study_id: Mapped[str] = mapped_column(String(36), ForeignKey("study.id", ondelete="CASCADE"), primary_key=True)
    area1: Mapped[str] = mapped_column(String, primary_key=True)
    area2: Mapped[str] = mapped_column(String, primary_key=True)

    hurdles_cost: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    loop_flow: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    use_phase_shifter: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    transmission_capacities: Mapped[TransmissionCapacity] = mapped_column(
        Enum(TransmissionCapacity), default=TransmissionCapacity.ENABLED, nullable=False
    )
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), default=AssetType.AC, nullable=False)
    display_comments: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    comments: Mapped[str] = mapped_column(String, default="", nullable=False)
    colorr: Mapped[int] = mapped_column(Integer, default=112, nullable=False)
    colorb: Mapped[int] = mapped_column(Integer, default=112, nullable=False)
    colorg: Mapped[int] = mapped_column(Integer, default=112, nullable=False)
    link_width: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    link_style: Mapped[LinkStyle] = mapped_column(Enum(LinkStyle), default=LinkStyle.PLAIN, nullable=False)
    filter_synthesis: Mapped[str] = mapped_column(String, default="hourly,daily,weekly,monthly,annual", nullable=False)
    filter_year_by_year: Mapped[str] = mapped_column(
        String, default="hourly,daily,weekly,monthly,annual", nullable=False
    )

    study: Mapped["Study"] = relationship("Study")
