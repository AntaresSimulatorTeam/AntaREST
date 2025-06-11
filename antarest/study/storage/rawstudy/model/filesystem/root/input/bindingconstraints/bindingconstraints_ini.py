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
from antarest.core.serde.ini_common import any_section_option_matcher
from antarest.core.serde.ini_reader import LOWER_CASE_PARSER, STRING_PARSER, IniReader
from antarest.core.serde.ini_writer import LOWER_CASE_SERIALIZER, IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode

_VALUE_PARSERS = {
    any_section_option_matcher("group"): LOWER_CASE_PARSER,
    any_section_option_matcher("id"): STRING_PARSER,
}
_VALUE_SERIALIZERS = {any_section_option_matcher("group"): LOWER_CASE_SERIALIZER}


# noinspection SpellCheckingInspection
class BindingConstraintsIni(IniFileNode):
    """
    Handle the binding constraints configuration file: `/input/bindingconstraints/bindingconstraints.ini`.

    This files contains a list of sections numbered from 1 to n.

    Each section contains the following fields:

    - `name`: the name of the binding constraint.
    - `id`: the id of the binding constraint (normalized name in lower case).
    - `enabled`: whether the binding constraint is enabled or not.
    - `type`: the frequency of the binding constraint ("hourly", "daily" or "weekly")
    - `operator`: the operator of the binding constraint ("both", "equal", "greater", "less")
    - `comment`: a comment
    - and a list of coefficients (one per line) of the form `{area1}%{area2} = {coeff}`.
    """

    def __init__(self, config: FileStudyTreeConfig):
        super().__init__(
            config,
            types={},
            reader=IniReader(value_parsers=_VALUE_PARSERS),
            writer=IniWriter(value_serializers=_VALUE_SERIALIZERS),
        )
