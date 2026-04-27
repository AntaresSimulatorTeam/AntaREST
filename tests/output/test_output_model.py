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
from antarest.output.model import (
    AreaAndLinkVariables,
    AreaVariables,
    McAllVar,
    OutputVariablesList,
    to_str_variables_list,
)


def test_output_model_conversion():
    input = OutputVariablesList(
        mc_ind=AreaAndLinkVariables(areas=[], links=[]),
        mc_all=AreaAndLinkVariables(
            areas=[
                AreaVariables(
                    name="fr",
                    variables=[McAllVar(name="Test Var", unit="MW", stat="EXP")],
                    thermal_clusters=[],
                    renewable_clusters=[],
                    short_term_storages=[],
                )
            ],
            links=[],
        ),
    )

    assert to_str_variables_list(input) == "toto"
