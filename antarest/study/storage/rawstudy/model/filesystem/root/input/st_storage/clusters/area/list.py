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

from antarest.core.serde.ini_common import any_section_option_matcher
from antarest.core.serde.ini_reader import LOWER_CASE_PARSER, IniReader
from antarest.core.serde.ini_writer import LOWER_CASE_SERIALIZER, IniWriter, ValueSerializer
from antarest.study.model import STUDY_VERSION_8_6
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode

_VALUE_PARSERS = {any_section_option_matcher("group"): LOWER_CASE_PARSER}


def _write_group_8_6(input: str) -> str:
    """
    The solver was not case insensitive to group, before version 8.6.
    We need to write it with a capital first letter.
    """
    return input.title()


def _get_group_serializer(study_version: StudyVersion) -> ValueSerializer:
    if study_version <= STUDY_VERSION_8_6:
        return _write_group_8_6
    else:
        return LOWER_CASE_SERIALIZER


class InputSTStorageAreaList(IniFileNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        # The list.ini file contains one section per short-term storage object associated to the area.
        # Every section contains the following properties :
        # - a name (str)
        # - a group (Possible values: "PSP_open", "PSP_closed", "Pondage", "Battery", "Other_1", ..., "Other_5", default = Other_1)
        # - an efficiency coefficient (double in range 0-1)
        # - a reservoir capacity (double > 0)
        # - an initial level (double in range 0-1)
        # - an initial_level_optim (bool, default = False)
        # - a withdrawal nominal capacity (double > 0)
        # - an injection nominal capacity (double > 0)
        types = {st_storage_id: dict for st_storage_id in config.get_st_storage_ids(area)}
        value_serializers = {any_section_option_matcher("group"): _get_group_serializer(config.version)}
        super().__init__(
            context,
            config,
            types,
            reader=IniReader(value_parsers=_VALUE_PARSERS),
            writer=IniWriter(value_serializers=value_serializers),
        )
