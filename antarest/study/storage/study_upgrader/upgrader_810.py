from pathlib import Path

from antarest.study.storage.antares_configparser import AntaresConfigParser

GENERAL_DATA_PATH = Path("settings") / "generaldata.ini"


def upgrade_810(study_path: Path) -> None:
    config = AntaresConfigParser()
    config.read(study_path / GENERAL_DATA_PATH)
    config["other preferences"][
        "renewable-generation-modelling"
    ] = "aggregated"
    with open(study_path / GENERAL_DATA_PATH, "w") as configfile:
        config.write(configfile)
    study_path.joinpath("input", "renewables", "clusters").mkdir(parents=True)
    study_path.joinpath("input", "renewables", "series").mkdir(parents=True)
