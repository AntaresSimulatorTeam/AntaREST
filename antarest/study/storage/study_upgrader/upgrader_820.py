import glob
from pathlib import Path

import numpy
import pandas  # type: ignore


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
                    numpy.savetxt(
                        folder_path / f"{name}_parameters.txt",
                        df_parameters.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    numpy.savetxt(
                        folder_path / "capacities" / f"{name}_direct.txt",
                        df_direct.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    numpy.savetxt(
                        folder_path / "capacities" / f"{name}_indirect.txt",
                        df_indirect.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    (folder_path / f"{name}.txt").unlink()
