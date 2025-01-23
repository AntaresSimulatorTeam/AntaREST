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

from antarest.study.storage.rawstudy.ini_reader import LOWER_CASE_PARSER, IniReader, OptionKey
from antarest.study.storage.rawstudy.ini_writer import LOWER_CASE_SERIALIZER, IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import NAME_TO_ID_MATCHER, IniFileNode

_VALUE_PARSERS = {OptionKey(None, "group"): LOWER_CASE_PARSER}
_VALUE_SERIALIZERS = {OptionKey(None, "group"): LOWER_CASE_SERIALIZER}


class InputThermalClustersAreaList(IniFileNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        section = {
            "name": str,
            "group": str,
            "unitcount": int,
            "nominalcapacity": float,
            "market-bid-cost": float,
        }
        types = {th: section for th in config.get_thermal_ids(area)}
        super().__init__(
            context,
            config,
            types,
            reader=IniReader(value_parsers=_VALUE_PARSERS),
            writer=IniWriter(value_serializers=_VALUE_SERIALIZERS),
            section_matcher=NAME_TO_ID_MATCHER,
        )
