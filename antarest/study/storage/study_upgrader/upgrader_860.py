from pathlib import Path

from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import DUPLICATE_KEYS

# noinspection SpellCheckingInspection
GENERAL_DATA_PATH = "settings/generaldata.ini"


def upgrade_860(study_path: Path) -> None:
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    data = reader.read(study_path / GENERAL_DATA_PATH)
    data["adequacy patch"]["enable-first-step "] = True
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, study_path / GENERAL_DATA_PATH)

    study_path.joinpath("input", "st-storage", "clusters").mkdir(parents=True, exist_ok=True)
    study_path.joinpath("input", "st-storage", "series").mkdir(parents=True, exist_ok=True)
    list_areas = (
        study_path.joinpath("input", "areas", "list.txt").read_text(encoding="utf-8").splitlines(keepends=False)
    )
    for area_name in list_areas:
        area_id = transform_name_to_id(area_name)
        st_storage_path = study_path.joinpath("input", "st-storage", "clusters", area_id)
        st_storage_path.mkdir(parents=True, exist_ok=True)
        (st_storage_path / "list.ini").touch()

        hydro_series_path = study_path.joinpath("input", "hydro", "series", area_id)
        hydro_series_path.mkdir(parents=True, exist_ok=True)
        (hydro_series_path / "mingen.txt").touch()
