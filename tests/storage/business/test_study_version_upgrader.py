import filecmp
import glob
import os
import shutil
import tempfile
from pathlib import Path
from typing import List
from zipfile import ZipFile

import pandas
import pytest

from antarest.study.storage import study_version_upgrader
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)
from antarest.study.storage.study_version_upgrader import InvalidUpgrade
from antarest.study.storage.study_version_upgrader import (
    MAPPING_TRANSMISSION_CAPACITIES,
)


def test_end_to_end_upgrades(tmp_path: Path):
    cur_dir: Path = Path(__file__).parent
    path_study = cur_dir / "assets" / "little_study_700.zip"
    with ZipFile(path_study) as zip_output:
        zip_output.extractall(path=tmp_path)
    tmp_dir_before_upgrade = tempfile.mkdtemp(
        suffix="before_upgrade.tmp", prefix="", dir=cur_dir
    )
    shutil.copytree(tmp_path, tmp_dir_before_upgrade, dirs_exist_ok=True)
    old_values = get_old_settings_values(tmp_path)
    old_areas_values = get_old_area_values(tmp_path)
    study_version_upgrader.upgrade_study(tmp_path, 840)
    assert_study_antares_file_is_updated(tmp_path)
    assert_settings_are_updated(tmp_path, old_values)
    assert_inputs_are_updated(tmp_path, old_areas_values)
    assert (False, are_directories_the_same(tmp_path, tmp_dir_before_upgrade))
    shutil.rmtree(tmp_dir_before_upgrade)


def test_fails_because_of_versions_asked(tmp_path: Path):
    cur_dir: Path = Path(__file__).parent
    path_study = cur_dir / "assets" / "little_study_700.zip"
    with ZipFile(path_study) as zip_output:
        zip_output.extractall(path=tmp_path)
    with pytest.raises(
        InvalidUpgrade,
        match="The version 600 is not supported",
    ):
        study_version_upgrader.upgrade_study(tmp_path, 600)
    with pytest.raises(
        InvalidUpgrade,
        match="The version you asked for is the one you currently have",
    ):
        study_version_upgrader.upgrade_study(tmp_path, 700)
    path_other_study = cur_dir / "assets" / "little_study_720.zip"
    target_other_study = tmp_path / "other_study_for_test"
    with ZipFile(path_other_study) as zip_output:
        zip_output.extractall(path=target_other_study)
    with pytest.raises(
        InvalidUpgrade,
        match="Cannot downgrade your study version",
    ):
        study_version_upgrader.upgrade_study(target_other_study, 700)


def test_fallback_if_study_input_broken(tmp_path):
    cur_dir: Path = Path(__file__).parent
    path_study = cur_dir / "assets" / "broken_study_720.zip"
    with ZipFile(path_study) as zip_output:
        zip_output.extractall(path=tmp_path)
    tmp_dir_before_upgrade = tempfile.mkdtemp(
        suffix="before_upgrade.tmp", prefix="", dir=cur_dir
    )
    shutil.copytree(tmp_path, tmp_dir_before_upgrade, dirs_exist_ok=True)
    with pytest.raises(
        expected_exception=pandas.errors.EmptyDataError,
        match="No columns to parse from file",
    ):
        study_version_upgrader.upgrade_study(tmp_path, 840)
    assert (True, are_directories_the_same(tmp_path, tmp_dir_before_upgrade))
    shutil.rmtree(tmp_dir_before_upgrade)


def assert_study_antares_file_is_updated(tmp_path: Path) -> None:
    with open(
        tmp_path / "study.antares", mode="r", encoding="utf-8"
    ) as study_antares:
        lines = study_antares.readlines()
        assert lines[1] == "version = 840\n"
        assert len(lines) == 7


def assert_settings_are_updated(tmp_path: Path, old_values: List[str]) -> None:
    general_data_path = tmp_path / "settings" / "generaldata.ini"
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    data = reader.read(Path(general_data_path))
    general = data["general"]
    optimization = data["optimization"]
    adequacy_patch = data["adequacy patch"]
    other_preferences = data["other preferences"]
    assert general["geographic-trimming"] == old_values[0]
    assert general["custom-scenario"] == old_values[1]
    assert general["thematic-trimming"] is False
    assert optimization["include-exportstructure"] is False
    assert (
        optimization["include-unfeasible-problem-behavior"] == "error-verbose"
    )
    assert (
        other_preferences["hydro-heuristic-policy"]
        == "accommodate rule curves"
    )
    assert other_preferences["renewable-generation-modelling"] == "aggregated"
    assert adequacy_patch["include-adq-patch"] is False
    assert (
        adequacy_patch["set-to-null-ntc-between-physical-out-for-first-step"]
        is True
    )
    assert (
        adequacy_patch[
            "set-to-null-ntc-from-physical-out-to-physical-in-for-first-step"
        ]
        is True
    )
    assert (
        optimization["transmission-capacities"]
        == MAPPING_TRANSMISSION_CAPACITIES[old_values[2]]
    )
    assert "include-split-exported-mps" not in optimization


def get_old_settings_values(tmp_path: Path) -> List[str]:
    general_data_path = tmp_path / "settings" / "generaldata.ini"
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    data = reader.read(Path(general_data_path))
    filtering_value = data["general"]["filtering"]
    custom_ts_value = data["general"]["custom-ts-numbers"]
    transmission_capa_value = data["optimization"]["transmission-capacities"]
    return [filtering_value, custom_ts_value, transmission_capa_value]


def get_old_area_values(tmp_path: Path) -> dict:
    links = glob.glob(str(tmp_path / "input" / "links" / "*"))
    dico = {}
    for folder in links:
        all_txt = glob.glob(str(Path(folder) / "*.txt"))
        if len(all_txt) > 0:
            for txt in all_txt:
                new_txt = txt.replace(
                    str(tmp_path / "input" / "links"), ""
                ).replace(".txt", "")
                df = pandas.read_csv(txt, sep="\t", header=None)
                dico[new_txt] = df
    return dico


def assert_inputs_are_updated(tmp_path: Path, dico: dict) -> None:
    input_path = tmp_path / "input"
    assert (input_path / "renewables").is_dir() is True
    assert (input_path / "renewables" / "clusters").is_dir() is True
    assert (input_path / "renewables" / "series").is_dir() is True
    links = glob.glob(str(tmp_path / "input" / "links" / "*"))
    for folder in links:
        folder_path = Path(folder)
        all_txt = glob.glob(str(folder_path / "*.txt"))
        if len(all_txt) > 0:
            for txt in all_txt:
                df = pandas.read_csv(txt, sep="\t", header=None)
                old_txt = (
                    txt.replace(str(tmp_path / "input" / "links"), "")
                    .replace(".txt", "")
                    .replace("_parameters", "")
                )
                assert (
                    df.values.all() == dico[old_txt].iloc[:, 2:8].values.all()
                )
        capacities = glob.glob(str(folder_path / "capacities" / "*"))
        if len(capacities) > 0:
            for direction_txt in capacities:
                df_capacities = pandas.read_csv(
                    direction_txt, sep="\t", header=None
                )
                old_txt = direction_txt.replace(
                    str(tmp_path / "input" / "links"), ""
                ).replace(f"capacities{os.sep}", "")
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


def are_directories_the_same(dir1, dir2) -> bool:
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
        if not are_directories_the_same(new_dir1, new_dir2):
            return False
    return True
