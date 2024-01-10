import glob
from pathlib import Path

from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import DUPLICATE_KEYS

GENERAL_DATA_PATH = "settings/generaldata.ini"


def upgrade_830(study_path: Path) -> None:
    """
    Upgrade the study configuration to version 830.

    NOTE:
        The file `study.antares` is not upgraded here.

    Args:
        study_path: path to the study directory.
    """

    reader = IniReader(DUPLICATE_KEYS)
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
    for folder in areas:
        folder_path = Path(folder)
        if folder_path.is_dir():
            writer = IniWriter(special_keys=DUPLICATE_KEYS)
            writer.write(
                {"adequacy-patch": {"adequacy-patch-mode": "outside"}},
                folder_path / "adequacy_patch.ini",
            )
