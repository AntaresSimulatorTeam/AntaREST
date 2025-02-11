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
Common properties related to thermal and renewable clusters, and short-term storage.

In the near future, this set of classes may be used for solar, wind and hydro clusters.
"""

import functools
import typing as t
from typing import Any

from pydantic import Field

from antarest.core.serde import AntaresBaseModel
from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import ItemName


class ItemProperties(
    AntaresBaseModel,
    extra="forbid",
    validate_assignment=True,
    populate_by_name=True,
):
    """
    Common properties related to thermal and renewable clusters, and short-term storage.
    """

    name: ItemName


class ClusterProperties(ItemProperties):
    """
    Properties of a thermal or renewable cluster read from the configuration files.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.cluster import ClusterProperties

    >>> cl1 = ClusterProperties(name="cluster-01", group="group-A", enabled=True, unit_count=2, nominal_capacity=100)
    >>> (cl1.installed_capacity, cl1.enabled_capacity)
    (200.0, 200.0)

    >>> cl2 = ClusterProperties(name="cluster-01", group="group-A", enabled=False, unit_count=2, nominal_capacity=100)
    >>> (cl2.installed_capacity, cl2.enabled_capacity)
    (200.0, 0.0)
    """

    # Activity status:
    # - True: the plant may generate.
    # - False: not yet commissioned, moth-balled, etc.
    enabled: bool = Field(default=True, description="Activity status", title="Enabled")

    # noinspection SpellCheckingInspection
    unit_count: int = Field(
        default=1,
        ge=1,
        description="Unit count",
        alias="unitcount",
        title="Unit Count",
    )

    # noinspection SpellCheckingInspection
    nominal_capacity: float = Field(
        default=0.0,
        ge=0,
        description="Nominal capacity (MW per unit)",
        alias="nominalcapacity",
        title="Nominal Capacity",
    )

    @property
    def installed_capacity(self) -> float:
        # fields may contain `None` values if they are turned into `Optional` fields
        if self.unit_count is None or self.nominal_capacity is None:
            return 0.0
        return self.unit_count * self.nominal_capacity

    @property
    def enabled_capacity(self) -> float:
        # fields may contain `None` values if they are turned into `Optional` fields
        if self.enabled is None or self.installed_capacity is None:
            return 0.0
        return self.enabled * self.installed_capacity
