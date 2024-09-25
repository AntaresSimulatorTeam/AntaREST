# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antarest.study.storage.rawstudy.model.filesystem.config.model import EnrModelling
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.areas import InputAreas
from antarest.study.storage.rawstudy.model.filesystem.root.input.bindingconstraints.bindingcontraints import (
    BindingConstraints,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.commons.prepro_series import InputPreproSeries
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.hydro import InputHydro
from antarest.study.storage.rawstudy.model.filesystem.root.input.link.link import InputLink
from antarest.study.storage.rawstudy.model.filesystem.root.input.miscgen.miscgen import InputMiscGen
from antarest.study.storage.rawstudy.model.filesystem.root.input.renewables.renewable import ClusteredRenewables
from antarest.study.storage.rawstudy.model.filesystem.root.input.reserves.reserves import InputReserves
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.st_storage import InputSTStorage
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.thermal import InputThermal


class Input(FolderNode):
    """
    Handle the input folder which contains all the input data of the study.
    """

    def build(self) -> TREE:
        config = self.config

        # noinspection SpellCheckingInspection
        children: TREE = {
            "areas": InputAreas(self.context, config.next_file("areas")),
            "bindingconstraints": BindingConstraints(self.context, config.next_file("bindingconstraints")),
            "hydro": InputHydro(self.context, config.next_file("hydro")),
            "links": InputLink(self.context, config.next_file("links")),
            "load": InputPreproSeries(self.context, config.next_file("load"), "load_"),
            "misc-gen": InputMiscGen(self.context, config.next_file("misc-gen")),
            "reserves": InputReserves(self.context, config.next_file("reserves")),
            "solar": InputPreproSeries(self.context, config.next_file("solar"), "solar_"),
            "thermal": InputThermal(self.context, config.next_file("thermal")),
            "wind": InputPreproSeries(self.context, config.next_file("wind"), "wind_"),
        }

        has_renewables = config.version >= 810 and EnrModelling(config.enr_modelling) == EnrModelling.CLUSTERS
        if has_renewables:
            children["renewables"] = ClusteredRenewables(self.context, config.next_file("renewables"))

        if config.version >= 860:
            children["st-storage"] = InputSTStorage(self.context, config.next_file("st-storage"))

        return children
