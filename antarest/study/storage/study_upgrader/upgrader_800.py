from pathlib import Path
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)

GENERAL_DATA_PATH = "settings/generaldata.ini"


def upgrade_800(study_path: Path) -> None:
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    data = reader.read(study_path / GENERAL_DATA_PATH)
    data["other preferences"][
        "hydro-heuristic-policy"
    ] = "accommodate rule curves"
    data["optimization"]["include-exportstructure"] = False
    data["optimization"][
        "include-unfeasible-problem-behavior"
    ] = "error-verbose"
    data["general"]["custom-scenario"] = data["general"]["custom-ts-numbers"]
    del data["general"]["custom-ts-numbers"]
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, study_path / GENERAL_DATA_PATH)
