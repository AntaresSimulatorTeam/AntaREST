from pathlib import Path
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)

# noinspection SpellCheckingInspection
GENERAL_DATA_PATH = "settings/generaldata.ini"


def upgrade_850(study_path: Path) -> None:
    """
    Upgrade the study configuration to version 850.

    NOTE:
        The file `study.antares` is not upgraded here.

    Args:
        study_path: path to the study directory.
    """

    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    data = reader.read(study_path / GENERAL_DATA_PATH)
    # fmt: off
    data["adequacy patch"]["price-taking-order"] = "DENS"
    data["adequacy patch"]["include-hurdle-cost-csr"] = False
    data["adequacy patch"]["check-csr-cost-function"] = False
    data["adequacy patch"]["threshold-initiate-curtailment-sharing-rule"] = 0.0
    data["adequacy patch"]["threshold-display-local-matching-rule-violations"] = 0.0
    data["adequacy patch"]["threshold-csr-variable-bounds-relaxation"] = 3
    # fmt: on
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, study_path / GENERAL_DATA_PATH)
