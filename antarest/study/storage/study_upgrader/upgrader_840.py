from pathlib import Path

from antarest.study.storage.antares_configparser import AntaresConfigParser

GENERAL_DATA_PATH = Path("settings") / "generaldata.ini"
MAPPING_TRANSMISSION_CAPACITIES = {
    True: "local-values",
    False: "null-for-all-links",
    "infinite": "infinite-for-all-links",
}


def upgrade_840(study_path: Path) -> None:
    config = AntaresConfigParser()
    config.read(study_path / GENERAL_DATA_PATH)
    config["optimization"][
        "transmission-capacities"
    ] = MAPPING_TRANSMISSION_CAPACITIES[
        config["optimization"].getboolean("transmission-capacities")
    ]
    config.remove_option("optimization", "include-split-exported-mps")
    with open(study_path / GENERAL_DATA_PATH, "w") as configfile:
        config.write(configfile)
