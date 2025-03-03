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

from antares.study.version import StudyVersion

from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import (
    RenewableConfig,
    RenewableProperties,
    RenewablePropertiesType,
    create_renewable_properties,
)


@all_optional_model
@camel_case_model
class RenewableClusterUpdate(RenewableProperties):
    """
    Model representing the data structure required to edit an existing renewable cluster.
    """

    class Config:
        populate_by_name = True


@all_optional_model
@camel_case_model
class RenewableClusterCreation(RenewableProperties):
    """
    Model representing the data structure required to create a new Renewable cluster within a study.
    """

    class Config:
        populate_by_name = True

    def to_properties(self, study_version: StudyVersion) -> RenewablePropertiesType:
        values = self.model_dump(exclude_none=True)
        return create_renewable_properties(study_version=study_version, data=values)


@camel_case_model
class RenewableClusterOutput(RenewableConfig):
    """
    Model representing the output data structure to display the details of a renewable cluster.
    """
