from pathlib import Path
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)

GENERAL_DATA_PATH = "settings/generaldata.ini"
MAPPING_TRANSMISSION_CAPACITIES = {
    True: "local-values",
    False: "null-for-all-links",
    "infinite": "infinite-for-all-links",
}


def upgrade_840(study_path: Path) -> None:
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    data = reader.read(study_path / GENERAL_DATA_PATH)
    data["optimization"][
        "transmission-capacities"
    ] = MAPPING_TRANSMISSION_CAPACITIES[
        data["optimization"]["transmission-capacities"]
    ]
    del data["optimization"]["include-split-exported-mps"]
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, study_path / GENERAL_DATA_PATH)
