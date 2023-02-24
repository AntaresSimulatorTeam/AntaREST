from pathlib import Path
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)

GENERAL_DATA_PATH = "settings/generaldata.ini"
ADEQUACY_PATCH = "adequacy patch"


def upgrade_850(study_path: Path) -> None:
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    data = reader.read(study_path / GENERAL_DATA_PATH)
    data[ADEQUACY_PATCH]["price-taking-order"] = "DENS"
    data[ADEQUACY_PATCH]["include-hurdle-cost-csr"] = False
    data[ADEQUACY_PATCH]["check-csr-cost-function"] = False
    data[ADEQUACY_PATCH]["threshold-initiate-curtailment-sharing-rule"] = 0.0
    data[ADEQUACY_PATCH][
        "threshold-display-local-matching-rule-violations"
    ] = 0.0
    data[ADEQUACY_PATCH]["threshold-csr-variable-bounds-relaxation"] = 3
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, study_path / GENERAL_DATA_PATH)
