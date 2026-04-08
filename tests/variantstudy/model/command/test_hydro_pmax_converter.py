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

from antarest.study.business.model.config.compatibility_parameters_model import HydroPmax
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.convert_hydro_pmax import ConvertHydroPmax
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study


def test_hydro_pmax_converter_creates_and_cleans_matrices(
    empty_study_920: FileStudy, command_context: CommandContext
) -> None:
    study = empty_study_920
    dao = build_dao_from_file_study(study, command_context)
    study_version = study.config.version

    output = CreateArea(area_name="fr", command_context=command_context, study_version=study_version).apply(
        study_dao=dao
    )
    assert output.status, output.message

    study_path = study.config.study_path
    max_power = study_path / "input" / "hydro" / "common" / "capacity" / "maxpower_fr.txt.link"
    daily_gen = study_path / "input" / "hydro" / "common" / "capacity" / "maxDailyGenEnergy_fr.txt.link"
    daily_pump = study_path / "input" / "hydro" / "common" / "capacity" / "maxDailyPumpEnergy_fr.txt.link"
    hourly_gen = study_path / "input" / "hydro" / "series" / "fr" / "maxHourlyGenPower.txt.link"
    hourly_pump = study_path / "input" / "hydro" / "series" / "fr" / "maxHourlyPumpPower.txt.link"

    assert max_power.exists()
    assert not daily_gen.exists()
    assert not daily_pump.exists()
    assert not hourly_gen.exists()
    assert not hourly_pump.exists()

    output = ConvertHydroPmax(
        command_context=command_context,
        study_version=study_version,
        hydro_pmax=HydroPmax.HOURLY,
    ).apply(study_dao=dao)
    assert output.status, output.message

    assert max_power.exists()
    assert daily_gen.exists()
    assert daily_pump.exists()
    assert hourly_gen.exists()
    assert hourly_pump.exists()

    output = ConvertHydroPmax(
        command_context=command_context,
        study_version=study_version,
        hydro_pmax=HydroPmax.DAILY,
    ).apply(study_dao=dao)
    assert output.status, output.message

    assert max_power.exists()
    assert not daily_gen.exists()
    assert not daily_pump.exists()
    assert not hourly_gen.exists()
    assert not hourly_pump.exists()
