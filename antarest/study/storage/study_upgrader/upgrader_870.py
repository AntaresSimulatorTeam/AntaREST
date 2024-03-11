import glob
import os.path
from pathlib import Path
from typing import cast

import numpy as np
import numpy.typing as npt
import pandas

from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import DUPLICATE_KEYS


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
    binding_constraints_files = glob.glob(str(binding_constraints_path / "*.txt"))
    for file in binding_constraints_files:
        name = Path(file).stem
        if os.path.getsize(file) == 0:
            lt, gt, eq = pandas.Series(), pandas.Series(), pandas.Series()
        else:
            df = pandas.read_csv(file, sep="\t", header=None)
            lt, gt, eq = df.iloc[:, 0], df.iloc[:, 1], df.iloc[:, 2]
        for term, suffix in zip([lt, gt, eq], ["lt", "gt", "eq"]):
            # noinspection PyTypeChecker
            np.savetxt(
                binding_constraints_path / f"{name}_{suffix}.txt",
                cast(npt.NDArray[np.float64], term.values),
                delimiter="\t",
                fmt="%.6f",
            )
        Path(file).unlink()

    # Add property group for every section in .ini file
    ini_file_path = binding_constraints_path / "bindingconstraints.ini"
    reader = IniReader(DUPLICATE_KEYS)
    data = reader.read(ini_file_path)
    for key in list(data.keys()):
        data[key]["group"] = "default"
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, ini_file_path)

    # Add properties for thermal clusters in .ini file
    areas = glob.glob(str(study_path.joinpath("input/thermal/clusters/*")))
    for area in areas:
        ini_file_path = Path(area) / "list.ini"
        data = reader.read(ini_file_path)
        for key in list(data.keys()):
            data[key]["costgeneration"] = "SetManually"
            data[key]["efficiency"] = 100
            data[key]["variableomcost"] = 0
        writer.write(data, ini_file_path)
