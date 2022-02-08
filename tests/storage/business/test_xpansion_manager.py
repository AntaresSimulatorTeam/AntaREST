import os
import uuid
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from antarest.core.model import JSON
from antarest.study.business.xpansion_management import XpansionManager
from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)


def make_empty_study(tmpdir: Path, version: int) -> FileStudy:
    cur_dir: Path = Path(__file__).parent
    study_path = Path(tmpdir / str(uuid.uuid4()))
    os.mkdir(study_path)
    with ZipFile(
        cur_dir / "assets" / f"empty_study_{version}.zip"
    ) as zip_output:
        zip_output.extractall(path=study_path)
    config = ConfigPathBuilder.build(study_path, "1")
    return FileStudy(config, FileStudyTree(Mock(), config))


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "version,expected_output",
    [
        (
            720,
            {
                "settings": {
                    "optimality_gap": 1,
                    "max_iteration": "inf",
                    "uc_type": "expansion_fast",
                    "master": "integer",
                    "yearly-weights": "None",
                    "additional-constraints": "None",
                    "relaxed-optimality-gap": 1e6,
                    "cut-type": "average",
                    "ampl.solver": "cbc",
                    "ampl.presolve": 0,
                    "ampl.solve_bounds_frequency": 1000000,
                },
                "candidates": {},
                "capa": {},
            },
        ),
        (
            810,
            {
                "settings": {
                    "optimality_gap": 1,
                    "max_iteration": "inf",
                    "uc_type": "expansion_fast",
                    "master": "integer",
                    "yearly-weights": "None",
                    "additional-constraints": "None",
                    "relative_gap": 1e-12,
                    "solver": "Cbc",
                },
                "candidates": {},
                "capa": {},
            },
        ),
    ],
)
def test_create_configuration(
    tmp_path: Path, version: int, expected_output: JSON
):
    """
    Test the creation of a configuration.
    """
    empty_study = make_empty_study(tmp_path, version)
    raw_study_service = Mock(spec=RawStudyService)
    variant_study_service = Mock(spec=VariantStudyService)
    xpansion_manager = XpansionManager(
        study_storage_service=StudyStorageService(
            raw_study_service, variant_study_service
        ),
    )
    study = RawStudy(
        id="1", path=empty_study.config.study_path, version=version
    )
    raw_study_service.get_raw.return_value = empty_study
    raw_study_service.cache = Mock()

    with pytest.raises(ChildNotFoundError):
        empty_study.tree.get(["user", "expansion"], expanded=True, depth=9)

    xpansion_manager.create_xpansion_configuration(study)

    assert (
        empty_study.tree.get(["user", "expansion"], expanded=True, depth=9)
        == expected_output
    )
