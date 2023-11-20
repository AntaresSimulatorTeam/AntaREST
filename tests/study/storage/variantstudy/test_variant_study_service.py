import datetime
import re
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from sqlalchemy import create_engine  # type: ignore

from antarest.core.model import PublicMode
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, User
from antarest.matrixstore.repository import MatrixContentRepository
from antarest.matrixstore.service import SimpleMatrixService
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import RawStudy, StudyAdditionalData
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import STStorageConfig, STStorageGroup
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import with_db_context

# noinspection SpellCheckingInspection
EXPECTED_DENORMALIZED = {
    "Desktop.ini",
    "input/areas/fr/adequacy_patch.ini",
    "input/areas/fr/optimization.ini",
    "input/areas/fr/ui.ini",
    "input/areas/list.txt",
    "input/areas/sets.ini",
    "input/bindingconstraints/bindingconstraints.ini",
    "input/hydro/allocation/fr.ini",
    "input/hydro/common/capacity/creditmodulations_fr.txt.link",
    "input/hydro/common/capacity/inflowPattern_fr.txt.link",
    "input/hydro/common/capacity/maxpower_fr.txt.link",
    "input/hydro/common/capacity/reservoir_fr.txt.link",
    "input/hydro/common/capacity/waterValues_fr.txt.link",
    "input/hydro/hydro.ini",
    "input/hydro/prepro/correlation.ini",
    "input/hydro/prepro/fr/energy.txt.link",
    "input/hydro/prepro/fr/prepro.ini",
    "input/hydro/series/fr/mingen.txt.link",
    "input/hydro/series/fr/mod.txt.link",
    "input/hydro/series/fr/ror.txt.link",
    "input/links/fr/properties.ini",
    "input/load/prepro/correlation.ini",
    "input/load/prepro/fr/conversion.txt.link",
    "input/load/prepro/fr/data.txt.link",
    "input/load/prepro/fr/k.txt.link",
    "input/load/prepro/fr/settings.ini",
    "input/load/prepro/fr/translation.txt.link",
    "input/load/series/load_fr.txt.link",
    "input/misc-gen/miscgen-fr.txt.link",
    "input/renewables/clusters/fr/list.ini",
    "input/reserves/fr.txt.link",
    "input/solar/prepro/correlation.ini",
    "input/solar/prepro/fr/conversion.txt.link",
    "input/solar/prepro/fr/data.txt.link",
    "input/solar/prepro/fr/k.txt.link",
    "input/solar/prepro/fr/settings.ini",
    "input/solar/prepro/fr/translation.txt.link",
    "input/solar/series/solar_fr.txt.link",
    "input/st-storage/clusters/fr/list.ini",
    "input/st-storage/series/fr/storage1/PMAX-injection.txt.link",
    "input/st-storage/series/fr/storage1/PMAX-withdrawal.txt.link",
    "input/st-storage/series/fr/storage1/inflows.txt.link",
    "input/st-storage/series/fr/storage1/lower-rule-curve.txt.link",
    "input/st-storage/series/fr/storage1/upper-rule-curve.txt.link",
    "input/thermal/areas.ini",
    "input/thermal/clusters/fr/list.ini",
    "input/wind/prepro/correlation.ini",
    "input/wind/prepro/fr/conversion.txt.link",
    "input/wind/prepro/fr/data.txt.link",
    "input/wind/prepro/fr/k.txt.link",
    "input/wind/prepro/fr/settings.ini",
    "input/wind/prepro/fr/translation.txt.link",
    "input/wind/series/wind_fr.txt.link",
    "layers/layers.ini",
    "settings/comments.txt",
    "settings/generaldata.ini",
    "settings/resources/study.ico",
    "settings/scenariobuilder.dat",
    "study.antares",
}


class TestVariantStudyService:
    @pytest.mark.parametrize(
        "denormalize",
        [
            pytest.param(True, id="denormalize_yes"),
            pytest.param(False, id="denormalize_no"),
        ],
    )
    @pytest.mark.parametrize(
        "from_scratch",
        [
            pytest.param(True, id="from_scratch__yes"),
            pytest.param(False, id="from_scratch__no"),
        ],
    )
    @with_db_context
    def test_generate_task(
        self,
        tmp_path: Path,
        variant_study_service: VariantStudyService,
        raw_study_service: RawStudyService,
        simple_matrix_service: SimpleMatrixService,
        generator_matrix_constants: GeneratorMatrixConstants,
        patch_service: PatchService,
        study_storage_service: StudyStorageService,
        # pytest parameters
        denormalize: bool,
        from_scratch: bool,
    ) -> None:
        ## Prepare database objects
        # noinspection PyArgumentList
        user = User(id=0, name="admin")
        db.session.add(user)
        db.session.commit()

        # noinspection PyArgumentList
        group = Group(id="my-group", name="group")
        db.session.add(group)
        db.session.commit()

        ## First create a raw study (root of the variant)
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

        ## Prepare the RAW Study
        raw_study_service.create(raw_study)

        variant_study = variant_study_service.create_variant_study(
            raw_study.id,
            "My Variant Study",
            params=Mock(
                spec=RequestParameters,
                user=Mock(impersonator=user.id, is_site_admin=Mock(return_value=True)),
            ),
        )

        ## Prepare the RAW Study
        file_study = variant_study_service.get_raw(variant_study)

        command_context = CommandContext(
            generator_matrix_constants=generator_matrix_constants,
            matrix_service=simple_matrix_service,
            patch_service=patch_service,
        )

        create_area_fr = CreateArea(
            command_context=command_context,
            area_name="fr",
        )

        ## Prepare the Variant Study Data
        # noinspection SpellCheckingInspection
        pmax_injection = np.random.rand(8760, 1)
        inflows = np.random.uniform(0, 1000, size=(8760, 1))

        # noinspection PyArgumentList,PyTypeChecker
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id="fr",
            parameters=STStorageConfig(
                id="",  # will be calculated ;-)
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
        )

        execute_or_add_commands(
            variant_study,
            file_study,
            commands=[create_area_fr, create_st_storage],
            storage_service=study_storage_service,
        )

        ## Run the "generate" task
        actual_uui = variant_study_service.generate_task(
            variant_study,
            denormalize=denormalize,
            from_scratch=from_scratch,
        )
        assert re.fullmatch(
            r"[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}",
            actual_uui,
            flags=re.IGNORECASE,
        )

        ## Collect the resulting files
        workspaces = variant_study_service.config.storage.workspaces
        internal_studies_dir: Path = workspaces["default"].path
        snapshot_dir = internal_studies_dir.joinpath(variant_study.snapshot.id, "snapshot")
        res_study_files = {study_file.relative_to(snapshot_dir).as_posix() for study_file in snapshot_dir.rglob("*.*")}

        if denormalize:
            expected = {f.replace(".link", "") for f in EXPECTED_DENORMALIZED}
        else:
            expected = EXPECTED_DENORMALIZED
        assert res_study_files == expected
