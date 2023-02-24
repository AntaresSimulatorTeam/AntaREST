import glob
from pathlib import Path
from antarest.study.storage.antares_configparser import AntaresConfigParser
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)

GENERAL_DATA_PATH = "settings/generaldata.ini"


def upgrade_830(study_path: Path) -> None:
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    data = reader.read(study_path / GENERAL_DATA_PATH)
    data["adequacy patch"] = {
        "include-adq-patch": False,
        "set-to-null-ntc-between-physical-out-for-first-step": True,
        "set-to-null-ntc-from-physical-out-to-physical-in-for-first-step": True,
    }
    data["optimization"]["include-split-exported-mps"] = False
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, study_path / GENERAL_DATA_PATH)
    areas = glob.glob(str(study_path / "input" / "areas" / "*"))
    if len(areas) > 0:
        for folder in areas:
            folder_path = Path(folder)
            if folder_path.is_dir():
                config = AntaresConfigParser()
                config.read(
                    {"adequacy-patch": {"adequacy-patch-mode": "outside"}}
                )
                with open(folder_path / "adequacy_patch.ini", "w") as f:
                    config.write(f)
