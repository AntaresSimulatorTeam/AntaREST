import filecmp
import glob
import re
import shutil
import tempfile
from pathlib import Path
from typing import List
from zipfile import ZipFile

import pandas
import pytest


from antarest.study.storage.antares_configparser import AntaresConfigParser
from antarest.study.storage.study_upgrader import study_version_upgrader
from antarest.study.storage.study_upgrader import (
    InvalidUpgrade,
    UPGRADE_METHODS,
    MAPPING_TRANSMISSION_CAPACITIES,
)


def test_end_to_end_upgrades(tmp_path: Path):
    cur_dir: Path = Path(__file__).parent
    path_study = cur_dir / "assets" / "little_study_700.zip"
    with ZipFile(path_study) as zip_output:
        zip_output.extractall(path=tmp_path)
    tmp_dir_before_upgrade = tempfile.mkdtemp(
        suffix=".before_upgrade.tmp", prefix="~", dir=cur_dir / "assets"
    )
    shutil.copytree(tmp_path, tmp_dir_before_upgrade, dirs_exist_ok=True)
    old_values = get_old_settings_values(tmp_path)
    old_areas_values = get_old_area_values(tmp_path)
    # Only checks if the study_upgrader can go from the first supported version to the last one
    target_version = "850"
    study_version_upgrader.upgrade_study(tmp_path, target_version)
    with open(tmp_path / "settings" / "generaldata.ini", "r") as f:
        print(f.readlines())
    assert_study_antares_file_is_updated(tmp_path, target_version)
    assert_settings_are_updated(tmp_path, old_values)
    assert_inputs_are_updated(tmp_path, old_areas_values)
    assert (False, are_same_dir(tmp_path, tmp_dir_before_upgrade))
    shutil.rmtree(tmp_dir_before_upgrade)


def test_fails_because_of_versions_asked(tmp_path: Path):
    cur_dir: Path = Path(__file__).parent
    path_study = cur_dir / "assets" / "little_study_720.zip"
    with ZipFile(path_study) as zip_output:
        zip_output.extractall(path=tmp_path)
    with pytest.raises(
        InvalidUpgrade,
        match=f"Version '600' unknown: possible versions are {', '.join([u[1] for u in UPGRADE_METHODS])}",
    ):
        upgrade_study(tmp_path, "600")
    with pytest.raises(
        InvalidUpgrade, match="Your study is already in version '720'"
    ):
        upgrade_study(tmp_path, "720")
    with pytest.raises(
        InvalidUpgrade,
        match="Impossible to upgrade from version '720' to version '710'",
    ):
        upgrade_study(tmp_path, "710")
    with pytest.raises(
        InvalidUpgrade,
        match=f"Version '820.rc' unknown: possible versions are {', '.join([u[1] for u in UPGRADE_METHODS])}",
    ):
        upgrade_study(tmp_path, "820.rc")


def test_fallback_if_study_input_broken(tmp_path):
    cur_dir: Path = Path(__file__).parent
    path_study = cur_dir / "assets" / "broken_study_720.zip"
    with ZipFile(path_study) as zip_output:
        zip_output.extractall(path=tmp_path)
    tmp_dir_before_upgrade = tempfile.mkdtemp(
        suffix=".before_upgrade.tmp", prefix="~", dir=cur_dir / "assets"
    )
    shutil.copytree(tmp_path, tmp_dir_before_upgrade, dirs_exist_ok=True)
    with pytest.raises(
        expected_exception=pandas.errors.EmptyDataError,
        match="No columns to parse from file",
    ):
        study_version_upgrader.upgrade_study(tmp_path, "850")
    assert are_same_dir(tmp_path, tmp_dir_before_upgrade)
    shutil.rmtree(tmp_dir_before_upgrade)


def assert_study_antares_file_is_updated(
    tmp_path: Path, target_version: str
) -> None:
    lines = (tmp_path / "study.antares").read_text(encoding="utf-8")
    assert re.search(r"version\s*=\s*(\d+)", lines)[1] == target_version


def assert_settings_are_updated(tmp_path: Path, old_values: List[str]) -> None:
    general_data_path = tmp_path / "settings" / "generaldata.ini"
    config = AntaresConfigParser()
    config.read(Path(general_data_path))
    general = config["general"]
    optimization = config["optimization"]
    adequacy_patch = config["adequacy patch"]
    other_preferences = config["other preferences"]
    assert general["geographic-trimming"] == old_values[0]
    assert general["custom-scenario"] == old_values[1]
    assert general.getboolean("geographic-trimming") is False
    assert optimization.getboolean("include-exportstructure") is False
    assert (
        optimization["include-unfeasible-problem-behavior"] == "error-verbose"
    )
    assert (
        other_preferences["hydro-heuristic-policy"]
        == "accommodate rule curves"
    )
    assert other_preferences["renewable-generation-modelling"] == "aggregated"
    assert adequacy_patch.getboolean("include-adq-patch") is False
    assert adequacy_patch[
        "set-to-null-ntc-between-physical-out-for-first-step"
    ]
    assert adequacy_patch.getboolean(
        "set-to-null-ntc-from-physical-out-to-physical-in-for-first-step"
    )
    assert (
        optimization["transmission-capacities"]
        == MAPPING_TRANSMISSION_CAPACITIES[old_values[2]]
    )
    assert "include-split-exported-mps" not in optimization
    assert adequacy_patch["price-taking-order"] == "DENS"
    assert adequacy_patch.getboolean("include-hurdle-cost-csr") is False
    assert adequacy_patch.getboolean("check-csr-cost-function") is False
    assert (
        adequacy_patch.getfloat("threshold-initiate-curtailment-sharing-rule")
        == 0.0
    )
    assert (
        adequacy_patch.getfloat(
            "threshold-display-local-matching-rule-violations"
        )
        == 0.0
    )
    assert (
        adequacy_patch.getint("threshold-csr-variable-bounds-relaxation") == 3
    )


def get_old_settings_values(tmp_path: Path) -> List[str]:
    general_data_path = tmp_path / "settings" / "generaldata.ini"
    config = AntaresConfigParser()
    config.read(Path(general_data_path))
    filtering_value = config["general"]["filtering"]
    custom_ts_value = config["general"]["custom-ts-numbers"]
    transmission_capa_value = config["optimization"].getboolean(
        "transmission-capacities"
    )
    return [filtering_value, custom_ts_value, transmission_capa_value]


def get_old_area_values(tmp_path: Path) -> dict:
    links = glob.glob(str(tmp_path / "input" / "links" / "*"))
    dico = {}
    for folder in links:
        all_txt = glob.glob(str(Path(folder) / "*.txt"))
        if len(all_txt) > 0:
            for txt in all_txt:
                path_txt = Path(txt)
                new_txt = Path(path_txt.parent.name).joinpath(path_txt.stem)
                df = pandas.read_csv(txt, sep="\t", header=None)
                dico[str(new_txt)] = df
    return dico


def assert_inputs_are_updated(tmp_path: Path, dico: dict) -> None:
    input_path = tmp_path / "input"
    assert (input_path / "renewables").is_dir()
    assert (input_path / "renewables" / "clusters").is_dir()
    assert (input_path / "renewables" / "series").is_dir()
    links = glob.glob(str(tmp_path / "input" / "links" / "*"))
    for folder in links:
        folder_path = Path(folder)
        all_txt = glob.glob(str(folder_path / "*.txt"))
        if len(all_txt) > 0:
            for txt in all_txt:
                path_txt = Path(txt)
                old_txt = str(
                    Path(path_txt.parent.name).joinpath(path_txt.stem)
                ).replace("_parameters", "")
                df = pandas.read_csv(txt, sep="\t", header=None)
                assert (
                    df.values.all() == dico[old_txt].iloc[:, 2:8].values.all()
                )
        capacities = glob.glob(str(folder_path / "capacities" / "*"))
        if len(capacities) > 0:
            for direction_txt in capacities:
                df_capacities = pandas.read_csv(
                    direction_txt, sep="\t", header=None
                )
                direction_path = Path(direction_txt)
                old_txt = str(
                    Path(direction_path.parent.parent.name).joinpath(
                        direction_path.name
                    )
                )
                if "indirect" in old_txt:
                    new_txt = old_txt.replace("_indirect.txt", "")
                    assert (
                        df_capacities[0].values.all()
                        == dico[new_txt].iloc[:, 0].values.all()
                    )
                else:
                    new_txt = old_txt.replace("_direct.txt", "")
                    assert (
                        df_capacities[0].values.all()
                        == dico[new_txt].iloc[:, 1].values.all()
                    )


def are_same_dir(dir1, dir2) -> bool:
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if (
        len(dirs_cmp.left_only) > 0
        or len(dirs_cmp.right_only) > 0
        or len(dirs_cmp.funny_files) > 0
    ):
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False
    )
    if len(mismatch) > 0 or len(errors) > 0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        path_dir1 = Path(dir1)
        path_dir2 = Path(dir2)
        path_common_dir = Path(common_dir)
        new_dir1 = path_dir1 / path_common_dir
        new_dir2 = path_dir2 / path_common_dir
        if not are_same_dir(new_dir1, new_dir2):
            return False
    return True
