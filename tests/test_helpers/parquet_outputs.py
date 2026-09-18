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
"""Small simulator-shaped outputs with deliberately heterogeneous columns."""

import shutil
from pathlib import Path

from antarest.output.filestudy.matrixfiles import get_start_column
from antarest.output.filestudy.model import VariableDescription
from antarest.study.model import MatrixFrequency


def write_matrix(path: Path, frequency: MatrixFrequency, headers: list[VariableDescription], seed: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    offset = get_start_column(frequency)
    lines = ["test", "test", "test", ""]
    for k in range(3):
        lines.append("\t".join([""] * offset + [h.to_tuple()[k] for h in headers]))
    for step in range(3):
        values = ["N/A" if i == 0 and step == 1 else str(seed + 10 * i + step) for i in range(len(headers))]
        lines.append("\t".join([str(step + 1)] * offset + values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rich_output(target: Path) -> Path:
    source = Path(__file__).parents[1] / "output/data/20260810-1420eco-thermal_groups"
    target.mkdir(parents=True)
    for item in source.iterdir():
        if item.name != "economy":
            if item.is_dir():
                shutil.copytree(item, target / item.name)
            else:
                shutil.copyfile(item, target / item.name)
    for year in (0, 1, 2):
        base = target / "economy" / ("mc-all" if year == 0 else f"mc-ind/{year:05}")
        for frequency in MatrixFrequency:
            for n, area in enumerate(("@ all areas", "es", "fr")):
                headers = [
                    VariableDescription("LOAD", "MWh", "EXP" if year == 0 else None),
                    VariableDescription(area + "_ONLY", None, "std" if year == 0 else None),
                ]
                write_matrix(
                    base / "areas" / area / f"values-{frequency.value}.txt", frequency, headers, 100 * n + year
                )
                for detail in ("details", "details-res", "details-STstorage"):
                    # Interleave cluster columns: reconstruction must preserve file order.
                    headers = [
                        VariableDescription(area + "_a", "MWh", "EXP" if year == 0 else None),
                        VariableDescription(area + "_b", "MWh", "EXP" if year == 0 else None),
                        VariableDescription(area + "_a", "NP Cost - Euro", "std" if year == 0 else None),
                        VariableDescription(area + "_b", None, "max" if year == 0 else None),
                    ]
                    write_matrix(
                        base / "areas" / area / f"{detail}-{frequency.value}.txt",
                        frequency,
                        headers,
                        1000 + n * 100 + year,
                    )
            for n, link in enumerate(("es - fr", "fr - it")):
                headers = [
                    VariableDescription("FLOW", "MW", "EXP" if year == 0 else None),
                    VariableDescription(link + "_ONLY", "Euro", "min" if year == 0 else None),
                ]
                write_matrix(
                    base / "links" / link / f"values-{frequency.value}.txt", frequency, headers, 10000 + n * 100 + year
                )
            write_matrix(
                base / "binding_constraints" / f"bc-{frequency.value}.txt",
                frequency,
                [VariableDescription("MARG. COST", "Euro", "EXP" if year == 0 else None)],
                year,
            )
    return target
