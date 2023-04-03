import contextlib
import datetime
import uuid
from unittest.mock import Mock, patch, ANY, call

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from antarest.core.exceptions import (
    AllocationDataNotFound,
    AreaNotFound,
    MultipleAllocationDataFound,
)
from antarest.core.model import PublicMode
from antarest.dbmodel import Base
from antarest.login.model import User, Group
from antarest.study.business.allocation_management import (
    AllocationField,
    AllocationFormFields,
    AllocationMatrix,
    AllocationManager,
)
from antarest.study.business.area_management import AreaInfoDTO, AreaType
from antarest.study.model import Study, StudyContentStatus, RawStudy
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


class TestAllocationField:
    def test_init__nominal_case(self):
        field = AllocationField(area_id="NORTH", coefficient=1)
        assert field.area_id == "NORTH"
        assert field.coefficient == 1

    def test_init__camel_case_args(self):
        field = AllocationField(areaId="NORTH", coefficient=1)
        assert field.area_id == "NORTH"
        assert field.coefficient == 1

    def test_validation__ge_0(self):
        """Ensure `coefficient` is greater than or equal to 0"""
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            AllocationField(areaId="NORTH", coefficient=-1)


class TestAllocationFormFields:
    def test_init__nominal_case(self):
        fields = AllocationFormFields(
            allocation=[
                {"area_id": "NORTH", "coefficient": 0.75},
                {"area_id": "SOUTH", "coefficient": 0.25},
            ]
        )
        assert fields.allocation == [
            AllocationField(area_id="NORTH", coefficient=0.75),
            AllocationField(area_id="SOUTH", coefficient=0.25),
        ]

    def test_validation__coefficients_column_non_empty(self):
        """Check that the coefficients colum is non-empty"""
        with pytest.raises(ValueError, match="non-empty|not empty"):
            AllocationFormFields(allocation=[])

    def test_validation__coefficients_column_not_nul(self):
        """Check that the coefficients column is not nul"""
        with pytest.raises(ValueError, match="non-nul|not nul"):
            AllocationFormFields(
                allocation=[
                    {"area_id": "NORTH", "coefficient": 0},
                ]
            )


class TestAllocationMatrix:
    def test_init__nominal_case(self):
        field = AllocationMatrix(
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

    def test_validation__coefficients_matrix_non_empty_array(self):
        """Check that the coefficients matrix is a non-empty array"""
        # fmt: off
        with pytest.raises(ValueError, match="(?:not empty|non[ -]empty) array"):
            AllocationMatrix(
                index=[],
                columns=[],
                data=[],
            )
        # fmt: off

    def test_validation__coefficients_matrix_array_shape(self):
        """Check that the coefficients matrix is an array of shape 2×1"""
        with pytest.raises(ValueError, match=r"array of shape \d+×\d+"):
            AllocationMatrix(
                index=["fr", "de"],
                columns=["fr"],
                data=[[1, 2], [3, 4]],
            )

    def test_validation__coefficients_matrix_positive_or_nul(self):
        """Check that all coefficients matrix has positive or nul coefficients"""
        # fmt: off
        with pytest.raises(ValueError, match="positive or nul|greater than or equal to 0"):
            AllocationMatrix(
                index=["fr", "de"],
                columns=["fr", "de"],
                data=[
                    [1.0, -1],
                    [0.2, 0],
                ],
            )
        # fmt: on

    def test_validation__coefficients_array_has_no_non_null_values(self):
        """Check that the coefficients matrix have non-nul columns"""
        with pytest.raises(ValueError, match="(?:not nul|non-nul) columns"):
            AllocationMatrix(
                index=["fr", "de"],
                columns=["fr", "de"],
                data=[
                    [0, 8],
                    [0, 0],
                ],
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
    "antarest.study.business.allocation_management.execute_or_add_commands"
)


class TestAllocationManager:
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

    def test_get_allocation_matrix__nominal_case(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        allocation_cfg = {
            "n": {"[allocation]": {"n": 1}},
            "e": {"[allocation]": {"e": 3, "s": 1}},
            "s": {"[allocation]": {"s": 0.1, "n": 0.2, "w": 0.6}},
            "w": {"[allocation]": {"w": 1}},
        }
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=allocation_cfg),
        )

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "*"  # all areas
        manager = AllocationManager(study_storage_service)

        # run
        matrix = manager.get_allocation_matrix(
            all_areas=all_areas, study=study, area_id=area_id
        )

        # Check
        assert matrix == AllocationMatrix(
            index=["n", "e", "s", "w"],
            columns=["n", "e", "s", "w"],
            data=[
                [1.0, 0.0, 0.2, 0.0],
                [0.0, 3.0, 0.0, 0.0],
                [0.0, 1.0, 0.1, 0.0],
                [0.0, 0.0, 0.6, 1.0],
            ],
        )

    def test_get_allocation_matrix__allocation_data_not_found(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks with an empty allocation config
        allocation_cfg = {}
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=allocation_cfg),
        )

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "*"  # all areas
        manager = AllocationManager(study_storage_service)
        with pytest.raises(AllocationDataNotFound):
            manager.get_allocation_matrix(
                all_areas=all_areas, study=study, area_id=area_id
            )

    def test_get_field_values__nominal_case(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        allocation_data = {"[allocation]": {"s": 0.1, "n": 0.2, "w": 0.6}}
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=allocation_data),
        )

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "s"  # South
        manager = AllocationManager(study_storage_service)
        fields = manager.get_field_values(
            all_areas=all_areas, study=study, area_id=area_id
        )
        assert fields == AllocationFormFields(
            allocation=[
                AllocationField(areaId="s", coefficient=0.1),
                AllocationField(areaId="n", coefficient=0.2),
                AllocationField(areaId="w", coefficient=0.6),
            ]
        )

    def test_get_field_values__multiple_allocation_data_found(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks: North + South
        allocation_cfg = {
            "n": {"[allocation]": {"n": 1}},
            "s": {"[allocation]": {"s": 0.1, "n": 0.2, "w": 0.6}},
        }
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=allocation_cfg),
        )

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "n,s"  # North + South
        manager = AllocationManager(study_storage_service)
        with pytest.raises(MultipleAllocationDataFound):
            manager.get_field_values(
                all_areas=all_areas, study=study, area_id=area_id
            )

    def test_set_field_values__nominal_case(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "s"  # South
        manager = AllocationManager(study_storage_service)
        with patch(EXECUTE_OR_ADD_COMMANDS) as exe:
            manager.set_field_values(
                all_areas=all_areas,
                study=study,
                area_id=area_id,
                data=AllocationFormFields(
                    allocation=[
                        AllocationField(area_id="s", coefficient=2),
                        AllocationField(area_id="e", coefficient=3),
                        AllocationField(area_id="n", coefficient=4),
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
        assert cmd.target == f"input/hydro/allocation/{area_id}/[allocation]"
        assert cmd.data == {"s": 2.0, "e": 3.0, "n": 4.0}

    def test_set_field_values__area_not_found(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "n"  # South
        manager = AllocationManager(study_storage_service)

        with patch(EXECUTE_OR_ADD_COMMANDS) as exe:
            with pytest.raises(AreaNotFound):
                manager.set_field_values(
                    all_areas=all_areas,
                    study=study,
                    area_id=area_id,
                    data=AllocationFormFields(
                        allocation=[
                            AllocationField(
                                area_id="UNKNOWN", coefficient=3.14
                            ),
                        ]
                    ),
                )
        exe.assert_not_called()
