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

from sqlalchemy.orm import relationship  # type: ignore

# noinspection PyUnresolvedReferences
from antarest.core.persistence import Base as PersistenceBase
from antarest.core.tasks.model import TaskJob
from antarest.launcher.model import JobResult
from antarest.login.model import Identity

Base = PersistenceBase

# Define a one-to-many relationship with `JobResult`.
# If an identity is deleted, all the associated job results are detached from the identity.
Identity.job_results = relationship(JobResult, back_populates="owner", cascade="save-update, merge")

# Define a one-to-many relationship with `TaskJob`.
# If an identity is deleted, all the associated task jobs are detached from the identity.
Identity.owned_jobs = relationship(TaskJob, back_populates="owner", cascade="save-update, merge")
