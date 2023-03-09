import contextlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest
from antarest.core.model import PublicMode
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    Patch,
    PatchArea,
    PatchOutputs,
    PatchStudy,
    RawStudy,
    Study,
    StudyAdditionalData,
)
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.patch_service import PatchService
from tests.conftest import with_db_context

PATCH_CONTENT = """ 
{
  "study": {
    "scenario": "BAU2025",
    "doc": null,
    "status": null,
    "comments": null,
    "tags": []
  },
  "areas": {
    "a1": {
      "country": "FR",
      "tags": []
    }
  },
  "thermal_clusters": null,
  "outputs": {
    "reference": "20210588-eco-1532"
    }
} 
    """


@pytest.mark.unit_test
class TestPatchService:
    @with_db_context
    @pytest.mark.parametrize("get_from_file", [True, False])
    @pytest.mark.parametrize("file_data", ["", PATCH_CONTENT])
    @pytest.mark.parametrize("patch_data", ["", PATCH_CONTENT])
    def test_get(
        self,
        tmp_path: Path,
        get_from_file: bool,
        file_data: str,
        patch_data: str,
    ):
        study_id = str(uuid.uuid4())

        if file_data:
            # create a "patch.json" file
            patch_json = tmp_path.joinpath("patch.json")
            patch_json.write_text(file_data, encoding="utf-8")

        # Prepare a RAW study
        # noinspection PyArgumentList
        raw_study = RawStudy(
            id=study_id,
            name="my_study",
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(tmp_path),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version="840",
            additional_data=StudyAdditionalData(
                author="john.doe",
                horizon="foo-horizon",
                patch=patch_data,
            ),
            archived=False,
            owner=None,
            groups=[],
            public_mode=PublicMode.NONE,
        )

        # Make sure the session is closed to avoid reusing DB objects
        with contextlib.closing(db.session):
            db.session.add(raw_study)
            db.session.commit()

        # The study must be fetched from the database
        raw_study: RawStudy = db.session.query(Study).get(study_id)

        # Create a PatchService which use a StudyMetadataRepository with a mocked cache
        patch_service = PatchService(
            repository=StudyMetadataRepository(Mock())
        )
        patch = patch_service.get(raw_study, get_from_file=get_from_file)

        # check the result
        if (get_from_file and file_data) or (
            not get_from_file and (patch_data or file_data)
        ):
            expected_patch = Patch(
                study=PatchStudy(scenario="BAU2025"),
                areas={"a1": PatchArea(country="FR")},
                outputs=PatchOutputs(reference="20210588-eco-1532"),
            )
        else:
            expected_patch = Patch()

        assert patch == expected_patch

    @with_db_context
    def test_save(self, tmp_path):
        study_id = str(uuid.uuid4())

        # Prepare a RAW study
        # noinspection PyArgumentList
        raw_study = RawStudy(
            id=study_id,
            name="my_study",
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(tmp_path),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version="840",
            additional_data=StudyAdditionalData(
                author="john.doe",
                horizon="foo-horizon",
                patch="",
            ),
            archived=False,
            owner=None,
            groups=[],
            public_mode=PublicMode.NONE,
        )

        # Make sure the session is closed to avoid reusing DB objects
        with contextlib.closing(db.session):
            db.session.add(raw_study)
            db.session.commit()

        # The study must be fetched from the database
        raw_study: RawStudy = db.session.query(Study).get(study_id)

        # Create a PatchService which use a StudyMetadataRepository with a mocked cache
        patch_service = PatchService(
            repository=StudyMetadataRepository(Mock())
        )

        patch = Patch(
            study=PatchStudy(scenario="BAU2025"),
            areas={"a1": PatchArea(country="FR")},
            outputs=PatchOutputs(reference="20210588-eco-1532"),
        )
        patch_service.save(raw_study, patch)

        # check the result
        actual_obj = json.loads(
            tmp_path.joinpath("patch.json").read_text(encoding="utf-8")
        )
        expected_obj = json.loads(PATCH_CONTENT)
        assert actual_obj == expected_obj

    @with_db_context
    def test_set_output_ref(self, tmp_path: Path):
        study_id = str(uuid.uuid4())

        patch_outputs = PatchOutputs(reference="some id")

        # Prepare a RAW study
        # noinspection PyArgumentList
        raw_study = RawStudy(
            id=study_id,
            name="my_study",
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(tmp_path),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version="840",
            additional_data=StudyAdditionalData(
                author="john.doe",
                horizon="foo-horizon",
                patch=patch_outputs.json(),
            ),
            archived=False,
            owner=None,
            groups=[],
            public_mode=PublicMode.NONE,
        )

        # Make sure the session is closed to avoid reusing DB objects
        with contextlib.closing(db.session):
            db.session.add(raw_study)
            db.session.commit()

        # The study must be fetched from the database
        raw_study: RawStudy = db.session.query(Study).get(study_id)

        # Create a PatchService which use a StudyMetadataRepository with a mocked cache
        patch_service = PatchService(
            repository=StudyMetadataRepository(Mock())
        )

        # run with status=True
        patch_service.set_reference_output(raw_study, "output-id", status=True)

        # check the result
        actual_obj = json.loads(
            tmp_path.joinpath("patch.json").read_text(encoding="utf-8")
        )
        expected_obj = json.loads(
            """
            {
              "areas": null,
              "outputs": {
                "reference": "output-id"
              },
              "study": null,
              "thermal_clusters": null
            }
            """
        )
        assert actual_obj == expected_obj

        # run with status=False
        patch_service.set_reference_output(
            raw_study, "output-id", status=False
        )
        actual_obj = json.loads(
            tmp_path.joinpath("patch.json").read_text(encoding="utf-8")
        )
        expected_obj = json.loads(
            """
            {
              "areas": null,
              "outputs": {
                "reference": null
              },
              "study": null,
              "thermal_clusters": null
            }
            """
        )
        assert actual_obj == expected_obj
