from pathlib import Path
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)

GENERAL_DATA_PATH = "settings/generaldata.ini"


def upgrade_710(study_path: Path) -> None:
    """
    Upgrade the study configuration to version 710.

    NOTE:
        The file `study.antares` is not upgraded here.

    Args:
        study_path: path to the study directory.
    """

    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    data = reader.read(study_path / GENERAL_DATA_PATH)
    data["general"]["geographic-trimming"] = data["general"]["filtering"]
    data["general"]["thematic-trimming"] = False
    data["optimization"]["link-type"] = "local"
    data["other preferences"]["hydro-pricing-mode"] = "fast"
    del data["general"]["filtering"]
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, study_path / GENERAL_DATA_PATH)
