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

"""
Object model used to read and update binding constraint configuration.
"""

from typing import Dict, List

from antarest.study.business.enum_ignore_case import EnumIgnoreCase


class BindingConstraintFrequency(EnumIgnoreCase):
    """
    Frequency of a binding constraint.

    Attributes:
        HOURLY: hourly time series with 8784 lines
        DAILY: daily time series with 366 lines
        WEEKLY: weekly time series with 366 lines (same as daily)
    """

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class BindingConstraintOperator(EnumIgnoreCase):
    """
    Operator of a binding constraint.

    Attributes:
        LESS: less than or equal to
        GREATER: greater than or equal to
        BOTH: both LESS and GREATER
        EQUAL: equal to
    """

    LESS = "less"
    GREATER = "greater"
    BOTH = "both"
    EQUAL = "equal"


OPERATOR_MATRICES_MAP: Dict[BindingConstraintOperator, List[str]] = {
    BindingConstraintOperator.EQUAL: ["eq"],
    BindingConstraintOperator.GREATER: ["gt"],
    BindingConstraintOperator.LESS: ["lt"],
    BindingConstraintOperator.BOTH: ["lt", "gt"],
}

OPERATOR_MATRIX_FILE_MAP = {
    BindingConstraintOperator.EQUAL: ["{bc_id}_eq"],
    BindingConstraintOperator.GREATER: ["{bc_id}_gt"],
    BindingConstraintOperator.LESS: ["{bc_id}_lt"],
    BindingConstraintOperator.BOTH: ["{bc_id}_lt", "{bc_id}_gt"],
}

DEFAULT_GROUP = "default"
"""Default group for binding constraints (since v8.7)."""
DEFAULT_OPERATOR = BindingConstraintOperator.EQUAL
DEFAULT_TIMESTEP = BindingConstraintFrequency.HOURLY
