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
from pydantic import ConfigDict, PositiveInt, RootModel

from antarest.core.serde import AntaresBaseModel


class PlaylistValues(AntaresBaseModel):
    status: bool = True  # True if the year is to be simulated by the solver, False otherwise
    weight: float | int = 1


class PlaylistValuesUpdate(AntaresBaseModel):
    status: bool | None = None
    weight: float | int | None = None


class PlaylistRootModel(RootModel[dict[int, PlaylistValues]]):
    model_config = ConfigDict(json_schema_extra={"example": {"1": {"status": False, "weight": 0.4}}})


class PlaylistUpdateRootModel(RootModel[dict[int, PlaylistValuesUpdate]]):
    model_config = ConfigDict(json_schema_extra={"example": {"1": {"status": False, "weight": 0.4}}})


class Playlist(AntaresBaseModel, extra="forbid"):
    years: dict[PositiveInt, PlaylistValues] = {}


class PlaylistUpdate(AntaresBaseModel, extra="forbid"):
    years: dict[PositiveInt, PlaylistValuesUpdate] = {}


def update_playlist(current: Playlist, new: PlaylistUpdate) -> Playlist:
    """
    Updates the playlist according to the provided update data.
    """
    current_playlist = current.model_dump()
    for year in new.years:
        new_properties = new.years[year].model_dump(exclude_none=True)
        current_playlist["years"][year].update(new_properties)
    return Playlist.model_validate(current_playlist)
