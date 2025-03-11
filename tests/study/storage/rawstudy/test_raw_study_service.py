# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import typing as t
import zipfile
from pathlib import Path

import numpy as np
import pytest

from antarest.core.model import PublicMode
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, User
from antarest.matrixstore.service import SimpleMatrixService
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import RawStudy, StudyAdditionalData
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageGroup,
    STStorageProperties,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageConfig,
    STStorageGroup,
    STStorageProperties,
)
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import with_db_context


class TestRawStudyService:
    # noinspection SpellCheckingInspection
    """
    This class uses the `db_middleware` instance which is automatically created
    for each test method (the fixture has `autouse=True`).
    """

    @pytest.mark.parametrize(
        "outputs",
        [
            pytest.param(True, id="outputs_yes"),
            pytest.param(False, id="no_outputs"),
        ],
    )
    @pytest.mark.parametrize(
        "output_filter",
        [
            # fmt:off
            pytest.param(None, id="no_filter"),
            pytest.param(["20230802-1425eco"], id="folder"),
            pytest.param(["20230802-1628eco"], id="zipped"),
            pytest.param(["20230802-1425eco", "20230802-1628eco"], id="both"),
            # fmt:on
        ],
    )
    @pytest.mark.parametrize(
        "denormalize",
        [
            pytest.param(True, id="denormalize_yes"),
            pytest.param(False, id="denormalize_no"),
        ],
    )
    @with_db_context
    def test_export_study_flat(
        self,
        tmp_path: Path,
        raw_study_service: RawStudyService,
        simple_matrix_service: SimpleMatrixService,
        generator_matrix_constants: GeneratorMatrixConstants,
        study_storage_service: StudyStorageService,
        # pytest parameters
        outputs: bool,
        output_filter: t.Optional[t.List[str]],
        denormalize: bool,
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

        raw_study_path = tmp_path / "My RAW Study"
        # noinspection PyArgumentList
        raw_study = RawStudy(
            id="my_raw_study",
            name=raw_study_path.name,
            version="860",
            author="John Smith",
            created_at=datetime.datetime(2023, 7, 15, 16, 45),
            updated_at=datetime.datetime(2023, 7, 19, 8, 15),
            last_access=datetime.datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            path=str(raw_study_path),
            additional_data=StudyAdditionalData(author="John Smith"),
        )
        db.session.add(raw_study)
        db.session.commit()

        # Prepare the RAW Study
        raw_study_service.create(raw_study)
        file_study = raw_study_service.get_raw(raw_study)

        command_context = CommandContext(
            generator_matrix_constants=generator_matrix_constants,
            matrix_service=simple_matrix_service,
        )

        create_area_fr = CreateArea(command_context=command_context, area_name="fr", study_version=raw_study.version)

        # noinspection SpellCheckingInspection
        pmax_injection = np.random.rand(8760, 1)
        inflows = np.random.uniform(0, 1000, size=(8760, 1))

        # noinspection PyArgumentList,PyTypeChecker
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id="fr",
            parameters=STStorageProperties(
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

        execute_or_add_commands(
            raw_study,
            file_study,
            commands=[create_area_fr, create_st_storage],
            storage_service=study_storage_service,
        )

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
        src_outputs = set()
        for study_file in raw_study_path.rglob("*.*"):
            relpath = study_file.relative_to(raw_study_path).as_posix()
            if study_file.suffixes == [".txt", ".link"]:
                src_matrices.add(relpath.replace(".link", ""))
            elif relpath.startswith("output/"):
                src_outputs.add(relpath)
            else:
                src_study_files.add(relpath)

        # Run the export
        target_path = tmp_path / raw_study_path.with_suffix(".exported").name
        raw_study_service.export_study_flat(
            raw_study,
            target_path,
            outputs=outputs,
            output_list_filter=output_filter,
            denormalize=denormalize,
        )

        # Collect the resulting files
        res_study_files = set()
        res_matrices = set()
        res_outputs = set()
        for study_file in target_path.rglob("*.*"):
            relpath = study_file.relative_to(target_path).as_posix()
            if study_file.suffixes == [".txt", ".link"]:
                res_matrices.add(relpath.replace(".link", ""))
            elif relpath.startswith("output/"):
                res_outputs.add(relpath)
            else:
                res_study_files.add(relpath)

        # Check the matrice
        # If de-normalization is enabled, the previous loop won't find the matrices
        # because the matrix extensions are ".txt" instead of ".txt.link".
        # Therefore, it is necessary to move the corresponding ".txt" files
        # from `res_study_files` to `res_matrices`.
        if denormalize:
            assert not res_matrices, "All matrices must be denormalized"
            res_matrices = {f for f in res_study_files if f in src_matrices}
            res_study_files -= res_matrices
        assert res_matrices == src_matrices

        # Check the outputs
        if outputs:
            # If `outputs` is True the filtering can occurs
            if output_filter is None:
                expected_filter = {f.replace(".zip", "") for f in my_solver_outputs}
            else:
                expected_filter = set(output_filter)
            expected = {f"output/{output_name}/simulation.log" for output_name in expected_filter}
            assert res_outputs == expected
        else:
            # If `outputs` is False, no output must be exported
            # whatever the value of the `output_list_filter` is
            assert not res_outputs

        # Check the study files
        assert res_study_files == src_study_files
