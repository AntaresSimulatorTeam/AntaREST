import contextlib
import datetime
import uuid
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from antarest.core.exceptions import AllocationDataNotFound, AreaNotFound
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

from antarest.study.business.allocation_management import (
    AllocationManager,
    AllocationField,
    AllocationFormFields,
)


class TestAllocationField:
    def test_base(self):
        field = AllocationField(areaId="NORTH", coefficient=1)
        assert field.area_id == "NORTH"
        assert field.coefficient == 1

    def test_camel_case(self):
        field = AllocationField(areaId="NORTH", coefficient=1)
        assert field.dict(by_alias=True) == {
            "areaId": "NORTH",
            "coefficient": 1,
        }


class TestAllocationFormFields:
    def test_base_case(self):
        fields = AllocationFormFields(
            allocation=[
                {"areaId": "NORTH", "coefficient": 0.75},
                {"areaId": "SOUTH", "coefficient": 0.25},
            ]
        )
        assert fields.allocation == [
            AllocationField(areaId="NORTH", coefficient=0.75),
            AllocationField(areaId="SOUTH", coefficient=0.25),
        ]

    def test_fields_not_empty(self):
        """Check that the coefficients column is not empty"""
        with pytest.raises(ValueError, match="empty"):
            AllocationFormFields(
                allocation=[],
            )

    def test_validation_fields_no_duplicate_area_id(self):
        """Check that the coefficients column does not contain duplicate area IDs"""
        with pytest.raises(ValueError, match="duplicate"):
            AllocationFormFields(
                allocation=[
                    {"areaId": "NORTH", "coefficient": 0.75},
                    {"areaId": "NORTH", "coefficient": 0.25},
                ],
            )

    def test_validation_fields_no_negative_coefficient(self):
        """Check that the coefficients column does not contain negative coefficients"""
        with pytest.raises(ValueError, match="negative"):
            AllocationFormFields(
                allocation=[
                    {"areaId": "NORTH", "coefficient": 0.75},
                    {"areaId": "SOUTH", "coefficient": -0.25},
                ],
            )

    def test_validation_fields_no_negative_sum_coefficient(self):
        """Check that the coefficients values does not sum to negative"""
        with pytest.raises(ValueError, match="negative"):
            AllocationFormFields(
                allocation=[
                    {"areaId": "NORTH", "coefficient": -0.75},
                    {"areaId": "SOUTH", "coefficient": -0.25},
                ],
            )

    def test_validation_fields_no_nan_coefficient(self):
        """Check that the coefficients values does not contain NaN coefficients"""
        with pytest.raises(ValueError, match="NaN"):
            AllocationFormFields(
                allocation=[
                    {"areaId": "NORTH", "coefficient": 0.75},
                    {"areaId": "SOUTH", "coefficient": float("nan")},
                ],
            )


class TestAllocationMatrix:
    def test_base_case(self):
        field = AllocationMatrix(
            index=["NORTH", "SOUTH"],
            columns=["NORTH", "SOUTH"],
            data=[[0.75, 0.25], [0.25, 0.75]],
        )
        assert field.index == ["NORTH", "SOUTH"]
        assert field.columns == ["NORTH", "SOUTH"]
        assert field.data == [[0.75, 0.25], [0.25, 0.75]]

    def test_validation_coefficients_not_empty(self):
        """Check that the coefficients matrix is not empty"""
        with pytest.raises(ValueError, match="empty"):
            AllocationMatrix(
                index=[],
                columns=[],
                data=[],
            )

    def test_validation_matrix_shape(self):
        """Check that the coefficients matrix is square"""
        with pytest.raises(ValueError, match="square"):
            AllocationMatrix(
                index=["NORTH", "SOUTH"],
                columns=["NORTH"],
                data=[[0.75, 0.25], [0.25, 0.75]],
            )

    def test_validation_matrix_sum_positive(self):
        """Check that the coefficients matrix sum to positive"""
        with pytest.raises(ValueError, match="negative"):
            AllocationMatrix(
                index=["NORTH", "SOUTH"],
                columns=["NORTH", "SOUTH"],
                data=[[0.75, -0.25], [-0.25, 0.75]],
            )

    def test_validation_matrix_no_nan(self):
        """Check that the coefficients matrix does not contain NaN values"""
        with pytest.raises(ValueError, match="NaN"):
            AllocationMatrix(
                index=["NORTH", "SOUTH"],
                columns=["NORTH", "SOUTH"],
                data=[[0.75, 0.25], [0.25, float("nan")]],
            )

    def test_validation_matrix_no_non_null_values(self):
        """Check that the coefficients matrix does not contain only null values"""
        with pytest.raises(ValueError, match="(?:all|zero)"):
            AllocationMatrix(
                index=["NORTH", "SOUTH"],
                columns=["NORTH", "SOUTH"],
                data=[[0, 0], [0, 0]],
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

    def test_get_allocation_matrix__no_allocation(
        self, db_session, study_storage_service, study_uuid
    ):
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
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
        area_id = "*"
        manager = AllocationManager(study_storage_service)

        with pytest.raises(AllocationDataNotFound) as ctx:
            manager.get_allocation_matrix(
                all_areas=all_areas, study=study, area_id=area_id
            )
        assert "*" in ctx.value.detail

    def test_get_allocation_form_fields__nominal_case(
        self, db_session, study_storage_service, study_uuid
    ):
        study: RawStudy = db_session.query(Study).get(study_uuid)
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
            get=Mock(return_value=allocation_cfg["n"]),
        )

        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]

        area_id = "n"
        manager = AllocationManager(study_storage_service)

        fields = manager.get_allocation_form_fields(
            all_areas=all_areas, study=study, area_id=area_id
        )

        expected_allocation = [
            AllocationField.construct(area_id=area, coefficient=value)
            for area, value in allocation_cfg[area_id]["[allocation]"].items()
        ]
        assert fields.allocation == expected_allocation

    def test_get_allocation_form_fields__no_allocation_data(
        self, db_session, study_storage_service, study_uuid
    ):
        study: RawStudy = db_session.query(Study).get(study_uuid)
        allocation_cfg = {"n": {}}
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=allocation_cfg["n"]),
        )

        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
        ]

        area_id = "n"
        manager = AllocationManager(study_storage_service)

        with pytest.raises(AllocationDataNotFound) as ctx:
            manager.get_allocation_form_fields(
                all_areas=all_areas, study=study, area_id=area_id
            )
        assert "n" in ctx.value.detail

    def test_set_allocation_form_fields__nominal_case(
        self, db_session, study_storage_service, study_uuid
    ):
        study: RawStudy = db_session.query(Study).get(study_uuid)
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "n"
        manager = AllocationManager(study_storage_service)
        with patch(EXECUTE_OR_ADD_COMMANDS) as exe:
            with patch(
                "antarest.study.business.allocation_management.AllocationManager.get_allocation_data",
                return_value={"e": 0.5, "s": 0.25, "w": 0.25},
            ):
                manager.set_allocation_form_fields(
                    all_areas=all_areas,
                    study=study,
                    area_id=area_id,
                    data=AllocationFormFields.construct(
                        allocation=[
                            AllocationField.construct(
                                area_id="e", coefficient=0.5
                            ),
                            AllocationField.construct(
                                area_id="s", coefficient=0.25
                            ),
                            AllocationField.construct(
                                area_id="w", coefficient=0.25
                            ),
                        ],
                    ),
                )

        assert exe.call_count == 1
        mock_call = exe.mock_calls[0]
        actual_study, _, actual_commands, _ = mock_call.args
        assert actual_study == study
        assert len(actual_commands) == 1
        cmd: UpdateConfig = actual_commands[0]
        assert cmd.command_name == CommandName.UPDATE_CONFIG
        assert cmd.target == f"input/hydro/allocation/{area_id}/[allocation]"
        assert cmd.data == {"e": 0.5, "s": 0.25, "w": 0.25}

    def test_set_allocation_form_fields__no_allocation_data(
        self, db_session, study_storage_service, study_uuid
    ):
        study: RawStudy = db_session.query(Study).get(study_uuid)

        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]

        area_id = "n"
        manager = AllocationManager(study_storage_service)

        with patch(EXECUTE_OR_ADD_COMMANDS) as exe:
            with patch(
                "antarest.study.business.allocation_management.AllocationManager.get_allocation_data",
                side_effect=AllocationDataNotFound(area_id),
            ):
                with pytest.raises(AllocationDataNotFound) as ctx:
                    manager.set_allocation_form_fields(
                        all_areas=all_areas,
                        study=study,
                        area_id=area_id,
                        data=AllocationFormFields.construct(
                            allocation=[
                                AllocationField.construct(
                                    area_id="e", coefficient=0.5
                                ),
                                AllocationField.construct(
                                    area_id="s", coefficient=0.25
                                ),
                                AllocationField.construct(
                                    area_id="w", coefficient=0.25
                                ),
                            ],
                        ),
                    )
        assert "n" in ctx.value.detail

    def test_set_allocation_form_fields__invalid_area_ids(
        self, db_session, study_storage_service, study_uuid
    ):
        study: RawStudy = db_session.query(Study).get(study_uuid)

        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]

        area_id = "n"
        manager = AllocationManager(study_storage_service)

        data = AllocationFormFields.construct(
            allocation=[
                AllocationField.construct(area_id="e", coefficient=0.5),
                AllocationField.construct(area_id="s", coefficient=0.25),
                AllocationField.construct(
                    area_id="invalid_area", coefficient=0.25
                ),
            ]
        )

        with pytest.raises(AreaNotFound) as ctx:
            manager.set_allocation_form_fields(
                all_areas=all_areas, study=study, area_id=area_id, data=data
            )

        assert "invalid_area" in ctx.value.detail
