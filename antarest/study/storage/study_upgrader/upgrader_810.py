from pathlib import Path
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)

GENERAL_DATA_PATH = "settings/generaldata.ini"


def upgrade_810(study_path: Path) -> None:
    """
    Upgrade the study configuration to version 810.

    NOTE:
        The file `study.antares` is not upgraded here.

    Args:
        study_path: path to the study directory.
    """

    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    data = reader.read(study_path / GENERAL_DATA_PATH)
    data["other preferences"]["renewable-generation-modelling"] = "aggregated"
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, study_path / GENERAL_DATA_PATH)
    study_path.joinpath("input", "renewables", "clusters").mkdir(parents=True)
    study_path.joinpath("input", "renewables", "series").mkdir(parents=True)
