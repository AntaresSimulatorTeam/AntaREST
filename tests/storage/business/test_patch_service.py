import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.study.model import (
    Patch,
    PatchStudy,
    PatchArea,
    PatchOutputs,
)
from antarest.study.storage.patch_service import PatchService

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
def test_get(tmp_path: str):
    patch_json_path = Path(tmp_path) / "patch.json"
    patch_json_path.write_text(PATCH_CONTENT)
    raw_study = Mock()
    raw_study.path = tmp_path

    expected_patch = Patch(
        study=PatchStudy(scenario="BAU2025"),
        areas={"a1": PatchArea(country="FR")},
        outputs=PatchOutputs(reference="20210588-eco-1532"),
    )

    patch_service = PatchService()
    patch = patch_service.get(raw_study)
    assert patch == expected_patch


@pytest.mark.unit_test
def test_save(tmp_path: str):
    patch = Patch(
        study=PatchStudy(scenario="BAU2025"),
        areas={"a1": PatchArea(country="FR")},
        outputs=PatchOutputs(reference="20210588-eco-1532"),
    )
    expected_json = json.dumps(json.loads(PATCH_CONTENT))

    raw_study = Mock()
    raw_study.path = tmp_path

    patch_service = PatchService()
    patch_service.save(raw_study, patch)

    assert (Path(tmp_path) / "patch.json").read_text() == expected_json


@pytest.mark.unit_test
def test_set_output_ref(tmp_path: str):
    patch = Patch(
        study=PatchStudy(scenario="BAU2025"),
        areas={"a1": PatchArea(country="FR")},
        outputs=PatchOutputs(reference="20210588-eco-1532"),
    )

    raw_study = Mock()
    raw_study_patch = Patch(outputs=PatchOutputs(reference="some id"))

    patch_service = PatchService()
    patch_service.get = Mock(return_value=raw_study_patch)
    patch_service.save = Mock()

    expected = Patch(outputs=PatchOutputs(reference="output-id"))
    patch_service.set_reference_output(raw_study, "output-id", True)
    patch_service.save.assert_called_with(raw_study, expected)

    expected = Patch(outputs=PatchOutputs(reference=None))
    patch_service.set_reference_output(raw_study, "output-id", False)
    patch_service.save.assert_called_with(raw_study, expected)
