import filecmp
import glob
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import List

import pandas
import pytest

from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import DUPLICATE_KEYS
from antarest.study.storage.study_upgrader import UPGRADE_METHODS, InvalidUpgrade, upgrade_study
from antarest.study.storage.study_upgrader.upgrader_840 import MAPPING_TRANSMISSION_CAPACITIES
from tests.storage.business.assets import ASSETS_DIR


def test_end_to_end_upgrades(tmp_path: Path):
    # Prepare a study to upgrade
    path_study = ASSETS_DIR / "little_study_700.zip"
    study_dir = tmp_path / "little_study_700"
    with zipfile.ZipFile(path_study) as zip_output:
        zip_output.extractall(path=study_dir)
    # Backup the study before upgrade and read some values for later comparison
    before_upgrade_dir = tmp_path / "backup"
    shutil.copytree(study_dir, before_upgrade_dir, dirs_exist_ok=True)
    old_values = get_old_settings_values(study_dir)
    old_areas_values = get_old_area_values(study_dir)
    old_binding_constraint_values = get_old_binding_constraint_values(study_dir)
    # Only checks if the study_upgrader can go from the first supported version to the last one
    target_version = "880"
    upgrade_study(study_dir, target_version)
    assert_study_antares_file_is_updated(study_dir, target_version)
    assert_settings_are_updated(study_dir, old_values)
    assert_inputs_are_updated(study_dir, old_areas_values, old_binding_constraint_values)
    assert not are_same_dir(study_dir, before_upgrade_dir)


def test_fails_because_of_versions_asked(tmp_path: Path):
    # Prepare a study to upgrade
    path_study = ASSETS_DIR / "little_study_720.zip"
    study_dir = tmp_path / "little_study_720"
    with zipfile.ZipFile(path_study) as zip_output:
        zip_output.extractall(path=study_dir)
    # Try to upgrade with an unknown version
    with pytest.raises(
        InvalidUpgrade,
        match=f"Version '600' unknown: possible versions are {', '.join([u[1] for u in UPGRADE_METHODS])}",
    ):
        upgrade_study(study_dir, "600")
    # Try to upgrade with the current version
    with pytest.raises(InvalidUpgrade, match="Your study is already in version '720'"):
        upgrade_study(study_dir, "720")
    # Try to upgrade with an old version
    with pytest.raises(
        InvalidUpgrade,
        match="Impossible to upgrade from version '720' to version '710'",
    ):
        upgrade_study(study_dir, "710")
    # Try to upgrade with a version that does not exist
    with pytest.raises(
        InvalidUpgrade,
        match=f"Version '820.rc' unknown: possible versions are {', '.join([u[1] for u in UPGRADE_METHODS])}",
    ):
        upgrade_study(study_dir, "820.rc")


def test_fallback_if_study_input_broken(tmp_path):
    # Prepare a study to upgrade
    path_study = ASSETS_DIR / "broken_study_720.zip"
    study_dir = tmp_path / "broken_study_720"
    with zipfile.ZipFile(path_study) as zip_output:
        zip_output.extractall(path=study_dir)
    # Backup the study before upgrade and read some values for later comparison
    before_upgrade_dir = tmp_path / "backup"
    shutil.copytree(study_dir, before_upgrade_dir, dirs_exist_ok=True)
    with pytest.raises(
        expected_exception=pandas.errors.EmptyDataError,
        match="No columns to parse from file",
    ):
        upgrade_study(study_dir, "850")
    assert are_same_dir(study_dir, before_upgrade_dir)


def assert_study_antares_file_is_updated(tmp_path: Path, target_version: str) -> None:
    lines = (tmp_path / "study.antares").read_text(encoding="utf-8")
    assert re.search(r"version\s*=\s*(\d+)", lines)[1] == target_version


def assert_settings_are_updated(tmp_path: Path, old_values: List[str]) -> None:
    general_data_path = tmp_path / "settings" / "generaldata.ini"
    reader = IniReader(DUPLICATE_KEYS)
    data = reader.read(general_data_path)
    general = data["general"]
    optimization = data["optimization"]
    adequacy_patch = data["adequacy patch"]
    other_preferences = data["other preferences"]
    assert general["geographic-trimming"] == old_values[0]
    assert general["custom-scenario"] == old_values[1]
    assert general["geographic-trimming"] is False
    assert optimization["include-exportstructure"] is False
    assert optimization["include-unfeasible-problem-behavior"] == "error-verbose"
    assert other_preferences["hydro-heuristic-policy"] == "accommodate rule curves"
    assert other_preferences["renewable-generation-modelling"] == "aggregated"
    assert adequacy_patch["include-adq-patch"] is False
    assert adequacy_patch["set-to-null-ntc-between-physical-out-for-first-step"]
    assert adequacy_patch["set-to-null-ntc-from-physical-out-to-physical-in-for-first-step"]
    assert optimization["transmission-capacities"] == MAPPING_TRANSMISSION_CAPACITIES[old_values[2]]
    assert "include-split-exported-mps" not in optimization
    assert adequacy_patch["price-taking-order"] == "DENS"
    assert adequacy_patch["include-hurdle-cost-csr"] is False
    assert adequacy_patch["check-csr-cost-function"] is False
    assert adequacy_patch["threshold-initiate-curtailment-sharing-rule"] == 0.0
    assert adequacy_patch["threshold-display-local-matching-rule-violations"] == 0.0
    assert adequacy_patch["threshold-csr-variable-bounds-relaxation"] == 3
    assert adequacy_patch["enable-first-step"]


def get_old_settings_values(tmp_path: Path) -> List[str]:
    general_data_path = tmp_path / "settings" / "generaldata.ini"
    reader = IniReader(DUPLICATE_KEYS)
    data = reader.read(general_data_path)
    filtering_value = data["general"]["filtering"]
    custom_ts_value = data["general"]["custom-ts-numbers"]
    transmission_capa_value = data["optimization"]["transmission-capacities"]
    return [filtering_value, custom_ts_value, transmission_capa_value]


def get_old_area_values(tmp_path: Path) -> dict:
    dico = {}
    for folder in (tmp_path / "input" / "links").iterdir():
        all_txt = folder.glob("*.txt")
        for path_txt in all_txt:
            new_txt = Path(path_txt.parent.name).joinpath(path_txt.stem)
            df = pandas.read_csv(path_txt, sep="\t", header=None)
            dico[str(new_txt)] = df
    return dico


def get_old_binding_constraint_values(tmp_path: Path) -> dict:
    dico = {}
    bd_list = glob.glob(str(tmp_path / "input" / "bindingconstraints" / "*.txt"))
    for txt_file in bd_list:
        path_txt = Path(txt_file)
        df = pandas.read_csv(path_txt, sep="\t", header=None)
        dico[str(path_txt.stem)] = df
    return dico


def assert_inputs_are_updated(tmp_path: Path, old_area_values: dict, old_binding_constraint_values: dict) -> None:
    input_path = tmp_path / "input"

    # tests 8.1 upgrade
    assert_folder_is_created(input_path / "renewables")

    # tests 8.2 upgrade
    links = glob.glob(str(tmp_path / "input" / "links" / "*"))
    for folder in links:
        folder_path = Path(folder)
        for txt in folder_path.glob("*.txt"):
            path_txt = Path(txt)
            old_txt = str(Path(path_txt.parent.name).joinpath(path_txt.stem)).replace("_parameters", "")
            df = pandas.read_csv(txt, sep="\t", header=None)
            assert df.to_numpy().all() == old_area_values[old_txt].iloc[:, 2:8].values.all()
        capacities = glob.glob(str(folder_path / "capacities" / "*"))
        for direction_txt in capacities:
            df_capacities = pandas.read_csv(direction_txt, sep="\t", header=None)
            direction_path = Path(direction_txt)
            old_txt = str(Path(direction_path.parent.parent.name).joinpath(direction_path.name))
            if "indirect" in old_txt:
                new_txt = old_txt.replace("_indirect.txt", "")
                assert df_capacities[0].values.all() == old_area_values[new_txt].iloc[:, 0].values.all()
            else:
                new_txt = old_txt.replace("_direct.txt", "")
                assert df_capacities[0].values.all() == old_area_values[new_txt].iloc[:, 1].values.all()

    # tests 8.3 upgrade
    areas = glob.glob(str(tmp_path / "input" / "areas" / "*"))
    for folder in areas:
        folder_path = Path(folder)
        if folder_path.is_dir():
            reader = IniReader(DUPLICATE_KEYS)
            data = reader.read(folder_path / "adequacy_patch.ini")
            assert data["adequacy-patch"]["adequacy-patch-mode"] == "outside"

    # tests 8.6 upgrade
    assert_folder_is_created(input_path / "st-storage")
    list_areas = (input_path / "areas" / "list.txt").read_text(encoding="utf-8").splitlines(keepends=False)
    for area_name in list_areas:
        area_id = transform_name_to_id(area_name)
        st_storage_path = input_path.joinpath("st-storage", "clusters", area_id)
        assert st_storage_path.is_dir()
        assert (st_storage_path / "list.ini").exists()
        assert input_path.joinpath("hydro", "series", area_id, "mingen.txt").exists()

    # tests 8.7 upgrade
    # binding constraint part
    reader = IniReader(DUPLICATE_KEYS)
    data = reader.read(input_path / "bindingconstraints" / "bindingconstraints.ini")
    binding_constraints_list = list(data.keys())
    for bd in binding_constraints_list:
        bd_id = data[bd]["id"]
        assert data[bd]["group"] == "default"
        for k, term in enumerate(["lt", "gt", "eq"]):
            term_path = input_path / "bindingconstraints" / f"{bd_id}_{term}.txt"
            df = pandas.read_csv(term_path, sep="\t", header=None)
            assert df.to_numpy().all() == old_binding_constraint_values[bd_id].iloc[:, k].values.all()

    # thermal cluster part
    for area in list_areas:
        reader = IniReader(DUPLICATE_KEYS)
        thermal_series_path = tmp_path / "input" / "thermal" / "series" / area
        thermal_cluster_list = reader.read(tmp_path / "input" / "thermal" / "clusters" / area / "list.ini")
        for cluster in thermal_cluster_list:
            fuel_cost_path = thermal_series_path / cluster.lower() / "fuelCost.txt"
            co2_cost_path = thermal_series_path / cluster.lower() / "CO2Cost.txt"
            for path in [fuel_cost_path, co2_cost_path]:
                assert path.exists()
                assert os.path.getsize(path) == 0
            assert thermal_cluster_list[cluster]["costgeneration"] == "SetManually"
            assert thermal_cluster_list[cluster]["efficiency"] == 100
            assert thermal_cluster_list[cluster]["variableomcost"] == 0


def assert_folder_is_created(path: Path) -> None:
    assert path.is_dir()
    assert (path / "clusters").is_dir()
    assert (path / "series").is_dir()


def are_same_dir(dir1, dir2) -> bool:
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if len(dirs_cmp.left_only) > 0 or len(dirs_cmp.right_only) > 0 or len(dirs_cmp.funny_files) > 0:
        return False
    path_dir1 = Path(dir1)
    path_dir2 = Path(dir2)
    # check files content ignoring newline character (to avoid crashing on Windows)
    for common_file in dirs_cmp.common_files:
        file_1 = path_dir1 / common_file
        file_2 = path_dir2 / common_file
        # ignore study.ico
        if common_file == "study.ico":
            continue
        with open(file_1, "r", encoding="utf-8") as f1:
            with open(file_2, "r", encoding="utf-8") as f2:
                content_1 = f1.read().splitlines(keepends=False)
                content_2 = f2.read().splitlines(keepends=False)
                if content_1 != content_2:
                    return False
    # iter through common dirs recursively
    for common_dir in dirs_cmp.common_dirs:
        path_common_dir = Path(common_dir)
        new_dir1 = path_dir1 / path_common_dir
        new_dir2 = path_dir2 / path_common_dir
        if not are_same_dir(new_dir1, new_dir2):
            return False
    return True
