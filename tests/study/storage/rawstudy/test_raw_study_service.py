# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import datetime
import zipfile
from pathlib import Path

import numpy as np

from antarest.core.model import PublicMode
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.login.model import Group, User
from antarest.study.business.model.sts_model import STStorageCreation, STStorageGroup
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from tests.helpers import create_raw_study, with_admin_user, with_db_context

# noinspection SpellCheckingInspection
"""
This class uses the `db_middleware` instance which is automatically created
for each test method (the fixture has `autouse=True`).
"""


@with_db_context
@with_admin_user
def test_export_study_flat(
    tmp_path: Path, command_factory: CommandFactory, study_service: StudyService, fs_dao: FileStudyTreeDao
) -> None:
    # Prepare database objects
    # noinspection PyArgumentList
    user = User(id=0, name="admin")
    db.session.add(user)
    db.session.commit()

    # noinspection PyArgumentList
    group = Group(id="my-group", name="group")
    db.session.add(group)
    db.session.commit()

    raw_study_path = tmp_path / "my_study"  # Path used inside the `fs_dao` fixture
    # noinspection PyArgumentList
    raw_study = create_raw_study(
        id="my_raw_study",
        name=raw_study_path.name,
        version="860",
        author="John Smith",
        created_at=datetime.datetime(2023, 7, 15, 16, 45),
        updated_at=datetime.datetime(2023, 7, 19, 8, 15),
        last_access=current_time(),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
        path=str(raw_study_path),
    )
    db.session.add(raw_study)
    db.session.commit()

    # Create some data inside the study
    command_context = command_factory.command_context
    create_area_fr = CreateArea(command_context=command_context, area_name="fr", study_version=raw_study.version)

    # noinspection SpellCheckingInspection
    pmax_injection = np.random.rand(8760, 1)
    inflows = np.random.uniform(0, 1000, size=(8760, 1))

    # noinspection PyArgumentList,PyTypeChecker
    create_st_storage = CreateSTStorage(
        command_context=command_context,
        area_id="fr",
        parameters=STStorageCreation(
            name="Storage1",
            group=STStorageGroup.BATTERY,
            injection_nominal_capacity=1500,
            withdrawal_nominal_capacity=1500,
            reservoir_capacity=20000,
            efficiency=0.94,
            initial_level_optim=True,
        ),
        pmax_injection=pmax_injection.tolist(),
        inflows=inflows.tolist(),
        study_version=raw_study.version,
    )

    study_service.get_study_interface(raw_study).add_commands([create_area_fr, create_st_storage])

    # Prepare fake outputs
    my_solver_outputs = ["20230802-1425eco", "20230802-1628eco.zip"]
    for filename in my_solver_outputs:
        output_path = raw_study_path / "output" / filename
        # To simplify the checking, there is only one file in each output:
        if output_path.suffix.lower() == ".zip":
            # Create a fake ZIP file
            output_path.parent.mkdir(exist_ok=True, parents=True)
            with zipfile.ZipFile(
                output_path,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
            ) as zf:
                zf.writestr("simulation.log", data="Simulation done")
        else:
            # Create a directory
            output_path.mkdir(exist_ok=True, parents=True)
            (output_path / "simulation.log").write_text("Simulation done")

    # Collect all files by types to prepare the comparison
    src_study_files = set()
    src_matrices = set()
    for study_file in raw_study_path.rglob("*.*"):
        relpath = study_file.relative_to(raw_study_path).as_posix()
        if study_file.suffixes == [".txt", ".link"]:
            src_matrices.add(relpath.replace(".link", ""))
        elif not relpath.startswith("output/"):
            src_study_files.add(relpath)

    # Run the export
    target_path = tmp_path / raw_study_path.with_suffix(".exported").name
    study_service.storage_service.raw_study_service.export_study_flat(raw_study, target_path)

    # We should not export outputs
    assert not (target_path / "output").exists()

    # Collect the resulting files
    res_study_files = set()
    res_matrices = set()
    for study_file in target_path.rglob("*.*"):
        relpath = study_file.relative_to(target_path).as_posix()

        if study_file.suffixes != [".txt"] or study_file.name in {"comments.txt", "list.txt"}:
            res_study_files.add(relpath)
        else:
            res_matrices.add(relpath)

    assert res_matrices == src_matrices

    # Check the study files
    assert res_study_files == src_study_files
