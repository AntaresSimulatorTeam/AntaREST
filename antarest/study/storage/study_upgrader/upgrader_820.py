import glob
from pathlib import Path
from typing import cast

import numpy as np
import pandas
import numpy.typing as npt


def upgrade_820(study_path: Path) -> None:
    """
    Upgrade the study configuration to version 820.

    NOTE:
        The file `study.antares` is not upgraded here.

    Args:
        study_path: path to the study directory.
    """

    links = glob.glob(str(study_path / "input" / "links" / "*"))
    if len(links) > 0:
        for folder in links:
            folder_path = Path(folder)
            all_txt = glob.glob(str(folder_path / "*.txt"))
            if len(all_txt) > 0:
                (folder_path / "capacities").mkdir()
                for txt in all_txt:
                    df = pandas.read_csv(txt, sep="\t", header=None)
                    df_parameters = df.iloc[:, 2:8]
                    df_direct = df.iloc[:, 0]
                    df_indirect = df.iloc[:, 1]
                    name = Path(txt).stem
                    # noinspection PyTypeChecker
                    np.savetxt(
                        folder_path / f"{name}_parameters.txt",
                        cast(npt.NDArray[np.float64], df_parameters.values),
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    # noinspection PyTypeChecker
                    np.savetxt(
                        folder_path / "capacities" / f"{name}_direct.txt",
                        cast(npt.NDArray[np.float64], df_direct.values),
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    # noinspection PyTypeChecker
                    np.savetxt(
                        folder_path / "capacities" / f"{name}_indirect.txt",
                        cast(npt.NDArray[np.float64], df_indirect.values),
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    (folder_path / f"{name}.txt").unlink()
