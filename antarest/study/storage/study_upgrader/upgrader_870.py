import typing as t
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pandas as pd

from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.ini_writer import IniWriter


# noinspection SpellCheckingInspection
def upgrade_870(study_path: Path) -> None:
    """
    Upgrade the study configuration to version 870.

    NOTE:
        The file `study.antares` is not upgraded here.

    Args:
        study_path: path to the study directory.
    """

    # Split existing binding constraints in 3 different files
    binding_constraints_path = study_path / "input" / "bindingconstraints"
    binding_constraints_files = binding_constraints_path.glob("*.txt")
    for file in binding_constraints_files:
        name = file.stem
        if file.stat().st_size == 0:
            lt, gt, eq = pd.Series(), pd.Series(), pd.Series()
        else:
            df = pd.read_csv(file, sep="\t", header=None)
            lt, gt, eq = df.iloc[:, 0], df.iloc[:, 1], df.iloc[:, 2]
        for term, suffix in zip([lt, gt, eq], ["lt", "gt", "eq"]):
            # noinspection PyTypeChecker
            np.savetxt(
                binding_constraints_path / f"{name}_{suffix}.txt",
                t.cast(npt.NDArray[np.float64], term.values),
                delimiter="\t",
                fmt="%.6f",
            )
        file.unlink()

    # Add property group for every section in .ini file
    ini_file_path = binding_constraints_path / "bindingconstraints.ini"
    data = IniReader().read(ini_file_path)
    for section in data:
        data[section]["group"] = "default"
    IniWriter().write(data, ini_file_path)

    # Add properties for thermal clusters in .ini file
    ini_files = study_path.glob("input/thermal/clusters/*/list.ini")
    thermal_path = study_path / Path("input/thermal/series")
    for ini_file_path in ini_files:
        data = IniReader().read(ini_file_path)
        area_id = ini_file_path.parent.name
        for cluster in data:
            new_thermal_path = thermal_path / area_id / cluster.lower()
            (new_thermal_path / "CO2Cost.txt").touch()
            (new_thermal_path / "fuelCost.txt").touch()
            data[cluster]["costgeneration"] = "SetManually"
            data[cluster]["efficiency"] = 100
            data[cluster]["variableomcost"] = 0
        IniWriter().write(data, ini_file_path)
