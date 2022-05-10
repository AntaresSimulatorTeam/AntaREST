import os
import uuid
from io import StringIO
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from fastapi import UploadFile
from pandas.errors import ParserError

from antarest.core.model import JSON
from antarest.study.business.xpansion_management import (
    XpansionManager,
    XpansionSettingsDTO,
    XpansionCandidateDTO,
    LinkNotFound,
    ConstraintsNotFoundError,
    XpansionFileNotFoundError,
)
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
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
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


def make_xpansion_manager(empty_study):
    raw_study_service = Mock(spec=RawStudyService)
    variant_study_service = Mock(spec=VariantStudyService)
    xpansion_manager = XpansionManager(
        study_storage_service=StudyStorageService(
            raw_study_service, variant_study_service
        ),
    )
    raw_study_service.get_raw.return_value = empty_study
    raw_study_service.cache = Mock()
    return xpansion_manager


def make_areas(empty_study):
    CreateArea(
        area_name="area1", command_context=Mock(spec=CommandContext)
    )._apply_config(empty_study.config)
    CreateArea(
        area_name="area2", command_context=Mock(spec=CommandContext)
    )._apply_config(empty_study.config)


def make_link(empty_study):
    CreateLink(
        area1="area1", area2="area2", command_context=Mock(spec=CommandContext)
    )._apply_config(empty_study.config)


def make_link_and_areas(empty_study):
    make_areas(empty_study)
    make_link(empty_study)


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
                    "relaxed-optimality-gap": 1e6,
                    "cut-type": "yearly",
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
    study = RawStudy(
        id="1", path=empty_study.config.study_path, version=version
    )
    xpansion_manager = make_xpansion_manager(empty_study)

    with pytest.raises(ChildNotFoundError):
        empty_study.tree.get(["user", "expansion"], expanded=True, depth=9)

    xpansion_manager.create_xpansion_configuration(study)

    assert (
        empty_study.tree.get(["user", "expansion"], expanded=True, depth=9)
        == expected_output
    )


@pytest.mark.unit_test
def test_delete_xpansion_configuration(tmp_path: Path):
    """
    Test the deletion of a configuration.
    """
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)

    with pytest.raises(ChildNotFoundError):
        empty_study.tree.get(["user", "expansion"], expanded=True, depth=9)

    xpansion_manager.create_xpansion_configuration(study)

    assert empty_study.tree.get(["user", "expansion"], expanded=True, depth=9)

    xpansion_manager.delete_xpansion_configuration(study)

    with pytest.raises(ChildNotFoundError):
        empty_study.tree.get(["user", "expansion"], expanded=True, depth=9)


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "version,expected_output",
    [
        (
            720,
            XpansionSettingsDTO.parse_obj(
                {
                    "optimality_gap": 1,
                    "max_iteration": "inf",
                    "uc_type": "expansion_fast",
                    "master": "integer",
                    "yearly_weight": None,
                    "additional-constraints": None,
                    "relaxed-optimality-gap": 1000000.0,
                    "cut-type": "yearly",
                    "ampl.solver": "cbc",
                    "ampl.presolve": 0,
                    "ampl.solve_bounds_frequency": 1000000,
                    "relative_gap": None,
                    "solver": None,
                }
            ),
        ),
        (
            810,
            XpansionSettingsDTO.parse_obj(
                {
                    "optimality_gap": 1,
                    "max_iteration": "inf",
                    "uc_type": "expansion_fast",
                    "master": "integer",
                    "yearly_weight": None,
                    "additional-constraints": None,
                    "relaxed-optimality-gap": None,
                    "cut-type": None,
                    "ampl.solver": None,
                    "ampl.presolve": None,
                    "ampl.solve_bounds_frequency": None,
                    "relative_gap": 1e-12,
                    "solver": "Cbc",
                }
            ),
        ),
    ],
)
@pytest.mark.unit_test
def test_get_xpansion_settings(
    tmp_path: Path, version: int, expected_output: JSON
):
    """
    Test the retrieval of the xpansion settings.
    """

    empty_study = make_empty_study(tmp_path, version)
    study = RawStudy(
        id="1", path=empty_study.config.study_path, version=version
    )
    xpansion_manager = make_xpansion_manager(empty_study)

    xpansion_manager.create_xpansion_configuration(study)

    assert xpansion_manager.get_xpansion_settings(study) == expected_output


@pytest.mark.unit_test
def test_update_xpansion_settings(tmp_path: Path):
    """
    Test the retrieval of the xpansion settings.
    """

    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)

    xpansion_manager.create_xpansion_configuration(study)

    new_settings = XpansionSettingsDTO.parse_obj(
        {
            "optimality_gap": 4,
            "max_iteration": 123,
            "uc_type": "expansion_fast",
            "master": "integer",
            "yearly_weight": None,
            "additional-constraints": None,
            "relaxed-optimality-gap": None,
            "cut-type": None,
            "ampl.solver": None,
            "ampl.presolve": None,
            "ampl.solve_bounds_frequency": None,
            "relative_gap": 1e-12,
            "solver": "Cbc",
        }
    )

    xpansion_manager.update_xpansion_settings(study, new_settings)

    assert xpansion_manager.get_xpansion_settings(study) == new_settings


@pytest.mark.unit_test
def test_add_candidate(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    assert empty_study.tree.get(["user", "expansion", "candidates"]) == {}

    new_candidate = XpansionCandidateDTO.parse_obj(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    new_candidate2 = XpansionCandidateDTO.parse_obj(
        {
            "name": "candidate_2",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    with pytest.raises(KeyError):
        xpansion_manager.add_candidate(study, new_candidate)

    make_areas(empty_study)

    with pytest.raises(LinkNotFound):
        xpansion_manager.add_candidate(study, new_candidate)

    make_link(empty_study)

    xpansion_manager.add_candidate(study, new_candidate)

    candidates = {"1": new_candidate.dict(by_alias=True, exclude_none=True)}

    assert (
        empty_study.tree.get(["user", "expansion", "candidates"]) == candidates
    )

    xpansion_manager.add_candidate(study, new_candidate2)
    candidates["2"] = new_candidate2.dict(by_alias=True, exclude_none=True)

    assert (
        empty_study.tree.get(["user", "expansion", "candidates"]) == candidates
    )


@pytest.mark.unit_test
def test_get_candidate(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    assert empty_study.tree.get(["user", "expansion", "candidates"]) == {}

    new_candidate = XpansionCandidateDTO.parse_obj(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    new_candidate2 = XpansionCandidateDTO.parse_obj(
        {
            "name": "candidate_2",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    make_link_and_areas(empty_study)

    xpansion_manager.add_candidate(study, new_candidate)
    xpansion_manager.add_candidate(study, new_candidate2)

    assert (
        xpansion_manager.get_candidate(study, new_candidate.name)
        == new_candidate
    )
    assert (
        xpansion_manager.get_candidate(study, new_candidate2.name)
        == new_candidate2
    )


@pytest.mark.unit_test
def test_get_candidates(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    assert empty_study.tree.get(["user", "expansion", "candidates"]) == {}

    new_candidate = XpansionCandidateDTO.parse_obj(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    new_candidate2 = XpansionCandidateDTO.parse_obj(
        {
            "name": "candidate_2",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    make_link_and_areas(empty_study)

    xpansion_manager.add_candidate(study, new_candidate)
    xpansion_manager.add_candidate(study, new_candidate2)

    assert xpansion_manager.get_candidates(study) == [
        new_candidate,
        new_candidate2,
    ]


@pytest.mark.unit_test
def test_update_candidates(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    assert empty_study.tree.get(["user", "expansion", "candidates"]) == {}

    make_link_and_areas(empty_study)

    new_candidate = XpansionCandidateDTO.parse_obj(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )
    xpansion_manager.add_candidate(study, new_candidate)

    new_candidate2 = XpansionCandidateDTO.parse_obj(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )
    xpansion_manager.update_candidate(
        study, new_candidate.name, new_candidate2
    )

    assert (
        xpansion_manager.get_candidate(
            study, candidate_name=new_candidate.name
        )
        == new_candidate2
    )


@pytest.mark.unit_test
def test_delete_candidate(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    assert empty_study.tree.get(["user", "expansion", "candidates"]) == {}

    make_link_and_areas(empty_study)

    new_candidate = XpansionCandidateDTO.parse_obj(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )
    xpansion_manager.add_candidate(study, new_candidate)

    new_candidate2 = XpansionCandidateDTO.parse_obj(
        {
            "name": "candidate_2",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )
    xpansion_manager.add_candidate(study, new_candidate2)

    xpansion_manager.delete_candidate(study, new_candidate.name)

    assert xpansion_manager.get_candidates(study) == [new_candidate2]


@pytest.mark.unit_test
def test_update_constraints(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    with pytest.raises(XpansionFileNotFoundError):
        xpansion_manager.update_xpansion_constraints_settings(
            study=study, constraints_file_name="non_existent_file"
        )

    empty_study.tree.save({"user": {"expansion": {"constraints.txt": b"0"}}})

    xpansion_manager.update_xpansion_constraints_settings(
        study=study, constraints_file_name="constraints.txt"
    )

    assert (
        xpansion_manager.get_xpansion_settings(study).additional_constraints
        == "constraints.txt"
    )

    xpansion_manager.update_xpansion_constraints_settings(
        study=study, constraints_file_name=None
    )
    assert (
        xpansion_manager.get_xpansion_settings(study).additional_constraints
        is None
    )


@pytest.mark.unit_test
def test_add_constraints(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "constraints1.txt"
    filename2 = "constraints2.txt"
    content1 = "0"
    content2 = "1"

    upload_file_list = [
        UploadFile(filename=filename1, file=StringIO(content1)),
        UploadFile(filename=filename2, file=StringIO(content2)),
    ]

    xpansion_manager.add_xpansion_constraints(study, upload_file_list)

    assert filename1 in empty_study.tree.get(["user", "expansion"])
    assert content1.encode() == empty_study.tree.get(
        ["user", "expansion", filename1]
    )

    assert filename2 in empty_study.tree.get(["user", "expansion"])
    assert content2.encode() == empty_study.tree.get(
        ["user", "expansion", filename2]
    )


@pytest.mark.unit_test
def test_get_single_constraints(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    constraints_file_content = b"0"
    constraints_file_name = "constraints.txt"

    empty_study.tree.save(
        {
            "user": {
                "expansion": {constraints_file_name: constraints_file_content}
            }
        }
    )

    assert (
        xpansion_manager.get_single_xpansion_constraints(
            study, constraints_file_name
        )
        == constraints_file_content
    )


@pytest.mark.unit_test
def test_get_all_constraints(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "constraints1.txt"
    filename2 = "constraints2.txt"
    content1 = "0"
    content2 = "1"

    upload_file_list = [
        UploadFile(filename=filename1, file=StringIO(content1)),
        UploadFile(filename=filename2, file=StringIO(content2)),
    ]

    xpansion_manager.add_xpansion_constraints(study, upload_file_list)

    assert xpansion_manager.get_all_xpansion_constraints(study) == [
        filename1,
        filename2,
    ]


@pytest.mark.unit_test
def test_add_capa(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = "0"
    content2 = "1"

    upload_file_list = [
        UploadFile(filename=filename1, file=StringIO(content1)),
        UploadFile(filename=filename2, file=StringIO(content2)),
    ]

    xpansion_manager.add_capa(study, upload_file_list)

    assert filename1 in empty_study.tree.get(["user", "expansion", "capa"])
    assert {
        "columns": [0],
        "data": [[0.0]],
        "index": [0],
    } == empty_study.tree.get(["user", "expansion", "capa", filename1])

    assert filename2 in empty_study.tree.get(["user", "expansion", "capa"])
    assert {
        "columns": [0],
        "data": [[1.0]],
        "index": [0],
    } == empty_study.tree.get(["user", "expansion", "capa", filename2])


@pytest.mark.unit_test
def test_delete_capa(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = "0"
    content2 = "1"

    upload_file_list = [
        UploadFile(filename=filename1, file=StringIO(content1)),
        UploadFile(filename=filename2, file=StringIO(content2)),
    ]

    xpansion_manager.add_capa(study, upload_file_list)

    xpansion_manager.delete_capa(study, filename1)

    assert filename1 not in empty_study.tree.get(["user", "expansion", "capa"])

    assert filename2 in empty_study.tree.get(["user", "expansion", "capa"])


@pytest.mark.unit_test
def test_get_single_capa(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = "0"
    content2 = "3\nbc\td"

    upload_file_list = [
        UploadFile(filename=filename1, file=StringIO(content1)),
        UploadFile(filename=filename2, file=StringIO(content2)),
    ]

    xpansion_manager.add_capa(study, upload_file_list)

    assert xpansion_manager.get_single_capa(study, filename1) == {
        "columns": [0],
        "data": [[0.0]],
        "index": [0],
    }
    with pytest.raises(ParserError):
        xpansion_manager.get_single_capa(study, filename2)


@pytest.mark.unit_test
def test_get_all_capa(tmp_path: Path):
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = "0"
    content2 = "1"

    upload_file_list = [
        UploadFile(filename=filename1, file=StringIO(content1)),
        UploadFile(filename=filename2, file=StringIO(content2)),
    ]

    xpansion_manager.add_capa(study, upload_file_list)

    assert xpansion_manager.get_all_capa(study) == [filename1, filename2]
