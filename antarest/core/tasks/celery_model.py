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

"""
SQLAlchemy model for mapping TaskJob IDs to Celery task IDs.

This table is only used by the CeleryTaskService implementation
and is not part of the core TaskJob model.
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.persistence import Base


class CeleryTaskMapping(Base):
    """Maps an application TaskJob ID to its Celery AsyncResult ID."""

    __tablename__ = "celery_task_mapping"

    task_id: Mapped[str] = mapped_column(
        String(),
        ForeignKey("taskjob.id", name="fk_celery_mapping_taskjob_id", ondelete="CASCADE"),
        primary_key=True,
    )
    celery_id: Mapped[str] = mapped_column(String(), nullable=False)
