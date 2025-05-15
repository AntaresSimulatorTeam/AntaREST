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

from antarest.study.model import STUDY_VERSION_6_5
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class InputHydroIni(IniFileNode):
    # noinspection SpellCheckingInspection
    def __init__(self, config: FileStudyTreeConfig):
        # The "use heuristic", "follow load" and "reservoir capacity" parameters are missing here,
        # but are well taken into account in the `HydroManager` class and can be modified
        # by the user in the graphical interface.
        #
        # They are very used in the representation of hydro.
        # - "use heuristic" allows to define a reservoir management mode which consists
        #   in turbinating a certain fixed quantity each week.
        # - "reservoir capacity" is the capacity of the reservoir in MWh.
        # - "follow load" is a parameter whose activation (with others) helps to define
        #   the amount of water that can be turbinated for each reservoir each week.
        #   This amount depends on the consumption of the node on which the reservoir is located, hence the name.

        sections = [
            "inter-daily-breakdown",
            "intra-daily-modulation",
            "inter-monthly-breakdown",
            "reservoir",  # bool
            "use water",  # bool
            "hard bounds",  # bool
            "use leeway",  # bool
            "power to level",  # bool
        ]
        if config.version >= STUDY_VERSION_6_5:
            sections += [
                "initialize reservoir date",
                "leeway low",
                "leeway up",
                "pumping efficiency",
            ]
        section = {a: (int, float) for a in config.area_names()}
        types = {name: section for name in sections}

        IniFileNode.__init__(self, config, types)
