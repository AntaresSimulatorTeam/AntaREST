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

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class InputThermalClustersAreaReservesIni(IniFileNode):
    """
    INI file describing the participation of an area's thermal clusters to reserves.

    Each section corresponds to a single ``(cluster, reserve)`` participation. The
    section name uses the convention ``<cluster_id>__<reserve_id>``; this is required
    because the standard INI parser merges duplicate section names, so a unique
    composite key is used to address each participation independently.

    Examples
    --------

    [gas_cluster__reserve_1]
    cluster-name = gas_cluster
    max-power = 20.0
    max-power-off = 10.0
    participation-cost = 1.0
    participation-cost-off = 2.0
    """

    def __init__(self, config: FileStudyTreeConfig):
        IniFileNode.__init__(self, config)
