import glob
import json
import os
import typing
from datetime import datetime
from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path
from typing import Optional

import numpy
import pandas  # type: ignore

from antarest.core.exceptions import StudyValidationError
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)


def modify_file(
    study_path: str,
    file_path: str,
    key: str,
    parameter_to_add: Optional[str],
    value: typing.Any,
    parameter_to_delete: Optional[str],
) -> None:
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    file = glob.glob(os.path.join(study_path, file_path))[0]
    path = Path(file)
    data = reader.read(path)
    if key in data:
        if parameter_to_add is not None:
            data[key][parameter_to_add] = value
        if parameter_to_delete is not None:
            del data[key][parameter_to_delete]
    else:
        if parameter_to_add is not None:
            data[key] = {parameter_to_add: value}
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, path)


def find_value_in_file(
    study_path: str, file_path: str, key: str, parameter_to_check: str
) -> typing.Any:
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    file = glob.glob(os.path.join(study_path, file_path))[0]
    path = Path(file)
    data = reader.read(path)
    return data[key][parameter_to_check]


sep = os.sep
other_preferencies = "other preferences"
general_data_path = f"settings{sep}generaldata.ini"
adequacy_patch = "adequacy patch"
mapping_transmission_capacities = {
    True: "local-values",
    False: "null-for-all-links",
    "infinite": "infinite-for-all-links",
}


def upgrade_700(study_path: str) -> None:
    # It's the basecase study so we pass
    pass


def upgrade_710(study_path: str) -> None:
    geographical_trimming = find_value_in_file(
        study_path, general_data_path, "general", "filtering"
    )
    modify_file(
        study_path,
        general_data_path,
        "optimization",
        "link-type",
        "local",
        None,
    )
    modify_file(
        study_path,
        general_data_path,
        "general",
        "geographical-trimming",
        geographical_trimming,
        "filtering",
    )
    modify_file(
        study_path,
        general_data_path,
        "general",
        "thematic-trimming",
        False,
        None,
    )
    modify_file(
        study_path,
        general_data_path,
        other_preferencies,
        "hydro-pricing-mode",
        "fast",
        None,
    )


def upgrade_720(study_path: str) -> None:
    # There is no input modification between the 7.1.0 and the 7.2.0 version
    pass


def upgrade_800(study_path: str) -> None:
    custom_ts_numbers_value = find_value_in_file(
        study_path, general_data_path, "general", "custom-ts-numbers"
    )
    modify_file(
        study_path,
        general_data_path,
        other_preferencies,
        "hydro-heuristic-policy",
        "accommodate rule curves",
        None,
    )
    modify_file(
        study_path,
        general_data_path,
        "optimization",
        "include-exportstructure",
        False,
        None,
    )
    modify_file(
        study_path,
        general_data_path,
        "optimization",
        "include-infeasible-problem-behavior",
        "error-verbose",
        None,
    )
    modify_file(
        study_path,
        general_data_path,
        "general",
        "custom-scenario",
        custom_ts_numbers_value,
        "custom-ts-numbers",
    )


def upgrade_810(study_path: str) -> None:
    modify_file(
        study_path,
        general_data_path,
        other_preferencies,
        "renewable-generation-modelling",
        "aggregated",
        None,
    )
    os.mkdir(os.path.join(study_path + f"{sep}input", "renewables"))
    os.mkdir(
        os.path.join(study_path + f"{sep}input{sep}renewables", "clusters")
    )
    os.mkdir(os.path.join(study_path + f"{sep}input{sep}renewables", "series"))
    # TODO Cannot update study with renewables clusters for the moment


def upgrade_820(study_path: str) -> None:
    links = glob.glob(os.path.join(study_path, f"input{sep}links{sep}*"))
    if len(links) > 0:
        for folder in links:
            all_txt = glob.glob(os.path.join(folder, "*.txt"))
            if len(all_txt) > 0:
                os.mkdir(os.path.join(folder, "capacities"))
                for txt in all_txt:
                    df = pandas.read_csv(txt, sep="\t", header=None)
                    df_parameters = df.iloc[:, 2:8]
                    df_direct = df.iloc[:, 0]
                    df_indirect = df.iloc[:, 1]
                    reversed_txt = txt[::-1]
                    k = 0
                    while reversed_txt[k] != sep:
                        k += 1
                    name = reversed_txt[4:k][::-1]
                    numpy.savetxt(
                        folder + f"{sep}{name}_parameters.txt",
                        df_parameters.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    numpy.savetxt(
                        folder + f"{sep}capacities{sep}{name}_direct.txt",
                        df_direct.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    numpy.savetxt(
                        folder + f"{sep}capacities{sep}{name}_indirect.txt",
                        df_indirect.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    os.remove(folder + f"{sep}{name}.txt")


def upgrade_830(study_path: str) -> None:
    modify_file(
        study_path,
        general_data_path,
        "optimization",
        "include-split-exported-mps",
        False,
        None,
    )
    modify_file(
        study_path,
        general_data_path,
        adequacy_patch,
        "include-adq-patch",
        False,
        None,
    )
    modify_file(
        study_path,
        general_data_path,
        adequacy_patch,
        "set-to-null-ntc-between-physical-out-for-first-step",
        True,
        None,
    )
    modify_file(
        study_path,
        general_data_path,
        adequacy_patch,
        "set-to-null-ntc-from-physical-out-to-physical-in-for-first-step",
        True,
        None,
    )
    areas = glob.glob(os.path.join(study_path, f"input{sep}areas{sep}*"))
    if len(areas) > 0:
        for folder in areas:
            if Path(folder).is_dir():
                writer = IniWriter()
                writer.write(
                    {"adequacy-patch": {"adequacy-patch-mode": "outside"}},
                    Path(folder) / "adequacy_patch.ini",
                )


def upgrade_840(study_path: str) -> None:
    old_value = find_value_in_file(
        study_path,
        general_data_path,
        "optimization",
        "transmission-capacities",
    )
    modify_file(
        study_path,
        general_data_path,
        "optimization",
        None,
        None,
        "include-split-exported-mps",
    )
    modify_file(
        study_path,
        general_data_path,
        "optimization",
        "transmission-capacities",
        mapping_transmission_capacities[old_value],
        None,
    )


upgrade_methods = {
    700: upgrade_700,
    710: upgrade_710,
    720: upgrade_720,
    800: upgrade_800,
    810: upgrade_810,
    820: upgrade_820,
    830: upgrade_830,
    840: upgrade_840,
}


class InvalidUpgrade(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


def upgrade_study(study_path: str, new_version: int) -> None:
    old_version = get_current_version(study_path)
    check_upgrade_is_possible(old_version, new_version)
    return do_upgrade(study_path, old_version, new_version)


def get_current_version(study_path: str) -> int:
    file = glob.glob(os.path.join(study_path, "study.antares"))
    if len(file) != 1:
        raise StudyValidationError("The path of your study is not valid")
    f = open(file[0])
    for line in f:
        if "version" in line:
            return int(line[10:])
    raise StudyValidationError(
        "Your study.antares file is not in the good format"
    )


def check_upgrade_is_possible(old_version: int, new_version: int) -> None:
    if new_version not in upgrade_methods.keys():
        raise InvalidUpgrade(f"The version {new_version} is not supported")
    if old_version < 700 or new_version < 700:
        raise InvalidUpgrade(
            "Sorry the first version we deal with is the 7.0.0"
        )
    elif old_version > new_version:
        raise InvalidUpgrade("Cannot downgrade your study version")
    elif old_version == new_version:
        raise InvalidUpgrade(
            "The version you asked for is the one you currently have"
        )


def update_study_antares_file(new_version: int, study_path: str) -> None:
    epoch_time = datetime(1970, 1, 1)
    delta = int((datetime.now() - epoch_time).total_seconds())
    file = glob.glob(os.path.join(study_path, "study.antares"))[0]
    with open(file, "r") as f:
        lines = f.readlines()
        lines[1] = f"version = {new_version}\n"
        lines[4] = f"lastsave = {delta}\n"
    with open(file, "w") as f:
        for item in lines:
            f.write(item)
    f.close()


def do_upgrade(study_path: str, old_version: int, new_version: int) -> None:
    update_study_antares_file(new_version, study_path)
    possibilities = list(upgrade_methods.keys())
    start = 0
    end = len(possibilities) - 1
    while possibilities[start] != old_version:
        start += 1
    while possibilities[end] != new_version:
        end -= 1
    return recursive_changes(possibilities[start + 1 : end + 1], study_path)


def recursive_changes(update_list: typing.List[int], study_path: str) -> None:
    if len(update_list) > 0:
        elt = update_list[0]
        upgrade_methods[elt](study_path)
        recursive_changes(update_list[1:], study_path)
