import glob
from pathlib import Path

from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import DUPLICATE_KEYS


# noinspection SpellCheckingInspection
def upgrade_880(study_path: Path) -> None:
    """
    Upgrade the study configuration to version 880.

    NOTE:
        The file `study.antares` is not upgraded here.

    Args:
        study_path: path to the study directory.
    """
    st_storage_path = study_path / "input" / "st-storage" / "clusters"
    if not st_storage_path.exists():
        # The folder only exists for studies in v8.6+ that have some short term storage clusters.
        # For every other case, this upgrader has nothing to do.
        return
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    cluster_files = glob.glob(str(st_storage_path / "*" / "list.ini"))
    for file in cluster_files:
        file_path = Path(file)
        cluster_list = IniReader().read(file_path)
        for cluster in cluster_list:
            cluster_list[cluster]["enabled"] = True
        writer.write(cluster_list, file_path)
