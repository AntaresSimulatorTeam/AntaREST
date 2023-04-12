import contextlib
import datetime
import uuid
from unittest.mock import Mock, patch

import numpy as np
import pytest
from antarest.core.exceptions import AreaNotFound
from antarest.core.model import PublicMode
from antarest.dbmodel import Base
from antarest.login.model import Group, User
from antarest.study.business.area_management import AreaInfoDTO, AreaType
from antarest.study.business.correlation_management import (
    CorrelationField,
    CorrelationFormFields,
    CorrelationManager,
    CorrelationMatrix,
)
from antarest.study.model import RawStudy, Study, StudyContentStatus
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestCorrelationField:
    def test_init__nominal_case(self):
        field = CorrelationField(area_id="NORTH", coefficient=100)
        assert field.area_id == "NORTH"
        assert field.coefficient == 100

    def test_init__camel_case_args(self):
        field = CorrelationField(areaId="NORTH", coefficient=100)
        assert field.area_id == "NORTH"
        assert field.coefficient == 100


class TestCorrelationFormFields:
    def test_init__nominal_case(self):
        fields = CorrelationFormFields(
            correlation=[
                {"area_id": "NORTH", "coefficient": 75},
                {"area_id": "SOUTH", "coefficient": 25},
            ]
        )
        assert fields.correlation == [
            CorrelationField(area_id="NORTH", coefficient=75),
            CorrelationField(area_id="SOUTH", coefficient=25),
        ]

    def test_validation__coefficients_not_empty(self):
        """correlation must not be empty"""
        with pytest.raises(ValueError, match="must not be empty"):
            CorrelationFormFields(correlation=[])

    def test_validation__coefficients_no_duplicates(self):
        """correlation must not contain duplicate area IDs:"""
        with pytest.raises(ValueError, match="duplicate area IDs") as ctx:
            CorrelationFormFields(
                correlation=[
                    {"area_id": "NORTH", "coefficient": 50},
                    {"area_id": "NORTH", "coefficient": 25},
                    {"area_id": "SOUTH", "coefficient": 25},
                ]
            )
        assert "NORTH" in str(ctx.value)  # duplicates

    @pytest.mark.parametrize("coefficient", [-101, 101, np.nan])
    def test_validation__coefficients_invalid_values(self, coefficient):
        """coefficients must be between -100 and 100"""
        with pytest.raises(
            ValueError, match="between -100 and 100|must not contain NaN"
        ):
            CorrelationFormFields(
                correlation=[
                    {"area_id": "NORTH", "coefficient": coefficient},
                ]
            )


class TestCorrelationMatrix:
    def test_init__nominal_case(self):
        field = CorrelationMatrix(
            index=["fr", "de"],
            columns=["fr"],
            data=[
                [1.0],
                [0.2],
            ],
        )
        assert field.index == ["fr", "de"]
        assert field.columns == ["fr"]
        assert field.data == [
            [1.0],
            [0.2],
        ]

    def test_validation__coefficients_non_empty_array(self):
        """Check that the coefficients matrix is a non-empty array"""
        # fmt: off
        with pytest.raises(ValueError, match="must not be empty"):
            CorrelationMatrix(
                index=[],
                columns=[],
                data=[],
            )
        # fmt: off

    def test_validation__coefficients_array_shape(self):
        """Check that the coefficients matrix is an array of shape 2×1"""
        with pytest.raises(ValueError, match=r"must have shape \(\d+×\d+\)"):
            CorrelationMatrix(
                index=["fr", "de"],
                columns=["fr"],
                data=[[1, 2], [3, 4]],
            )

    @pytest.mark.parametrize("coefficient", [-1.1, 1.1, np.nan])
    def test_validation__coefficients_invalid_value(self, coefficient):
        """Check that all coefficients matrix has positive or nul coefficients"""
        # fmt: off
        with pytest.raises(ValueError, match="between -1 and 1|must not contain NaN"):
            CorrelationMatrix(
                index=["fr", "de"],
                columns=["fr", "de"],
                data=[
                    [1.0, coefficient],
                    [0.2, 0],
                ],
            )
        # fmt: on

    def test_validation__matrix_not_symmetric(self):
        """Check that the correlation matrix is not symmetric"""
        with pytest.raises(ValueError, match=r"not symmetric"):
            CorrelationMatrix(
                index=["fr", "de"],
                columns=["fr", "de"],
                data=[[0.1, 0.2], [0.3, 0.4]],
            )


@pytest.fixture(scope="function", name="db_engine")
def db_engine_fixture():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function", name="db_session")
def db_session_fixture(db_engine):
    make_session = sessionmaker(bind=db_engine)
    with contextlib.closing(make_session()) as session:
        yield session


# noinspection SpellCheckingInspection
EXECUTE_OR_ADD_COMMANDS = (
    "antarest.study.business.correlation_management.execute_or_add_commands"
)


class TestCorrelationManager:
    @pytest.fixture(name="study_storage_service")
    def study_storage_service(self) -> StudyStorageService:
        """Return a mocked StudyStorageService."""
        return Mock(
            spec=StudyStorageService,
            variant_study_service=Mock(
                spec=VariantStudyService,
                command_factory=Mock(
                    spec=CommandFactory,
                    command_context=Mock(spec=CommandContext),
                ),
            ),
            get_storage=Mock(
                return_value=Mock(
                    spec=RawStudyService, get_raw=Mock(spec=FileStudy)
                )
            ),
        )

    # noinspection PyArgumentList
    @pytest.fixture(name="study_uuid")
    def study_uuid_fixture(self, db_session) -> str:
        user = User(id=0, name="admin")
        group = Group(id="my-group", name="group")
        raw_study = RawStudy(
            id=str(uuid.uuid4()),
            name="Dummy",
            version="850",
            author="John Smith",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            workspace="default",
            path="/path/to/study",
            content_status=StudyContentStatus.WARNING,
        )
        db_session.add(raw_study)
        db_session.commit()
        return raw_study.id

    def test_get_correlation_matrix__nominal_case(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        correlation_cfg = {
            "n%n": 0.1,
            "e%e": 0.3,
            "s%s": 0.1,
            "s%n": 0.2,
            "s%w": 0.6,
            "w%w": 0.1,
        }
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=correlation_cfg),
        )

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        manager = CorrelationManager(study_storage_service)

        # run
        matrix = manager.get_correlation_matrix(
            all_areas=all_areas, study=study, columns=[]
        )

        # Check
        assert matrix == CorrelationMatrix(
            index=["n", "e", "s", "w"],
            columns=["n", "e", "s", "w"],
            data=[
                [1.0, 0.0, 0.2, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.2, 0.0, 1.0, 0.6],
                [0.0, 0.0, 0.6, 1.0],
            ],
        )

    def test_get_field_values__nominal_case(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        # NOTE: "s%s" value is ignored
        correlation_cfg = {"s%s": 0.1, "n%s": 0.2, "w%n": 0.6}
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=correlation_cfg),
        )

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "s"  # South
        manager = CorrelationManager(study_storage_service)
        fields = manager.get_correlation_form_fields(
            all_areas=all_areas, study=study, area_id=area_id
        )
        assert fields == CorrelationFormFields(
            correlation=[
                CorrelationField(area_id="n", coefficient=20.0),
                CorrelationField(area_id="s", coefficient=100.0),
            ]
        )

    def test_set_field_values__nominal_case(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks: North + South
        correlation_cfg = {}
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=correlation_cfg),
        )

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "s"  # South
        manager = CorrelationManager(study_storage_service)
        with patch(EXECUTE_OR_ADD_COMMANDS) as exe:
            manager.set_correlation_form_fields(
                all_areas=all_areas,
                study=study,
                area_id=area_id,
                data=CorrelationFormFields(
                    correlation=[
                        CorrelationField(area_id="s", coefficient=100),
                        CorrelationField(area_id="e", coefficient=30),
                        CorrelationField(area_id="n", coefficient=40),
                    ]
                ),
            )

        # check update
        assert exe.call_count == 1
        mock_call = exe.mock_calls[0]
        # signature: execute_or_add_commands(study, file_study, commands, storage_service)
        actual_study, _, actual_cmds, _ = mock_call.args
        assert actual_study == study
        assert len(actual_cmds) == 1
        cmd: UpdateConfig = actual_cmds[0]
        assert cmd.command_name == CommandName.UPDATE_CONFIG
        assert cmd.target == "input/hydro/prepro/correlation/annual"
        assert cmd.data == {"e%s": 0.3, "n%s": 0.4}

    def test_set_field_values__area_not_found(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks: North + South
        correlation_cfg = {}
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=correlation_cfg),
        )

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "n"  # South
        manager = CorrelationManager(study_storage_service)

        with patch(EXECUTE_OR_ADD_COMMANDS) as exe:
            with pytest.raises(AreaNotFound) as ctx:
                manager.set_correlation_form_fields(
                    all_areas=all_areas,
                    study=study,
                    area_id=area_id,
                    data=CorrelationFormFields(
                        correlation=[
                            CorrelationField(
                                area_id="UNKNOWN", coefficient=3.14
                            ),
                        ]
                    ),
                )
            assert "'UNKNOWN'" in ctx.value.detail
        exe.assert_not_called()
