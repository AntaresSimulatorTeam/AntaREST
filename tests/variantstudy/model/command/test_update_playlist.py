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
import pytest

from antarest.study.business.model.config.playlist_model import PlaylistUpdate
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_playlist import UpdatePlaylist
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study


class TestUpdatePlaylist:
    def test_nominal_case(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        study = empty_study_880
        dao = build_dao_from_file_study(study, command_context)

        study.tree.save(5, ["settings", "generaldata", "general", "nbyears"])

        default_values = study.tree.get(["settings", "generaldata"])
        assert "playlist" not in default_values

        args = {"years": {1: {"status": False, "weight": 3.2}, 3: {"weight": 4}}}

        properties = PlaylistUpdate.model_validate(args)

        command = UpdatePlaylist(
            playlist=properties, command_context=command_context, study_version=study.config.version
        )
        output = command.apply(study_dao=dao)
        assert output.status

        playlist_config = study.tree.get(["settings", "generaldata", "playlist"])

        assert playlist_config == {
            "playlist_reset": True,
            "playlist_year -": [0],
            "playlist_year_weight": ["0,3.2", "2,4"],
        }

    def test_error_cases(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        study = empty_study_880
        dao = build_dao_from_file_study(study, command_context)

        # Try to give a negative value for the year
        args = {"years": {-1: {"status": False, "weight": 3.2}}}
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            UpdatePlaylist(playlist=args, command_context=command_context, study_version=study.config.version)

        # Try to give a value higher than `nbyears`
        args = {"years": {3: {"status": False, "weight": 3.2}}}
        properties = PlaylistUpdate.model_validate(args)

        command = UpdatePlaylist(
            playlist=properties, command_context=command_context, study_version=study.config.version
        )
        output = command.apply(study_dao=dao)
        assert not output.status
