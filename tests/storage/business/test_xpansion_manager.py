import io
import os
import typing as t
import uuid
import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import UploadFile
from pandas.errors import ParserError

from antarest.core.model import JSON
from antarest.study.business.xpansion_management import (
    CutType,
    FileCurrentlyUsedInSettings,
    LinkNotFound,
    Master,
    MaxIteration,
    Solver,
    UcType,
    XpansionCandidateDTO,
    XpansionFileNotFoundError,
    XpansionManager,
    XpansionResourceFileType,
    XpansionSensitivitySettingsDTO,
    XpansionSettingsDTO,
)
from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import ChildNotFoundError
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.storage.business.assets import ASSETS_DIR


def make_empty_study(tmpdir: Path, version: int) -> FileStudy:
    study_path = Path(tmpdir / str(uuid.uuid4()))
    os.mkdir(study_path)
    with zipfile.ZipFile(ASSETS_DIR / f"empty_study_{version}.zip") as zip_output:
        zip_output.extractall(path=study_path)
    config = build(study_path, "1")
    return FileStudy(config, FileStudyTree(Mock(), config))


def make_xpansion_manager(empty_study: FileStudy) -> XpansionManager:
    raw_study_service = Mock(spec=RawStudyService)
    variant_study_service = Mock(spec=VariantStudyService)
    xpansion_manager = XpansionManager(
        study_storage_service=StudyStorageService(raw_study_service, variant_study_service),
    )
    raw_study_service.get_raw.return_value = empty_study
    raw_study_service.cache = Mock()
    return xpansion_manager


def make_areas(empty_study: FileStudy) -> None:
    CreateArea(
        area_name="area1",
        command_context=Mock(spec=CommandContext, generator_matrix_constants=Mock()),
    )._apply_config(empty_study.config)
    CreateArea(
        area_name="area2",
        command_context=Mock(spec=CommandContext, generator_matrix_constants=Mock()),
    )._apply_config(empty_study.config)


def make_link(empty_study: FileStudy) -> None:
    CreateLink(
        area1="area1",
        area2="area2",
        command_context=Mock(spec=CommandContext, generator_matrix_constants=Mock()),
    )._apply_config(empty_study.config)


def make_link_and_areas(empty_study: FileStudy) -> None:
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
                    "max_iteration": "+Inf",
                    "uc_type": "expansion_fast",
                    "master": "integer",
                    "relaxed-optimality-gap": 1e6,
                    "cut-type": "yearly",
                    "ampl.solver": "cbc",
                    "ampl.presolve": 0,
                    "ampl.solve_bounds_frequency": 1000000,
                },
                "sensitivity": {"sensitivity_in": {}},
                "candidates": {},
                "capa": {},
                "constraints": {},
                "weights": {},
            },
        ),
        (
            810,
            {
                "settings": {
                    "optimality_gap": 1,
                    "max_iteration": "+Inf",
                    "uc_type": "expansion_fast",
                    "master": "integer",
                    "relative_gap": 1e-12,
                    "solver": "Cbc",
                    "batch_size": 0,
                    "separation_parameter": 0.5,
                },
                "sensitivity": {"sensitivity_in": {}},
                "candidates": {},
                "capa": {},
                "constraints": {},
                "weights": {},
            },
        ),
    ],
)
def test_create_configuration(tmp_path: Path, version: int, expected_output: JSON) -> None:
    """
    Test the creation of a configuration.
    """
    empty_study = make_empty_study(tmp_path, version)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=version)
    xpansion_manager = make_xpansion_manager(empty_study)

    with pytest.raises(ChildNotFoundError):
        empty_study.tree.get(["user", "expansion"], expanded=True, depth=9)

    xpansion_manager.create_xpansion_configuration(study)

    assert empty_study.tree.get(["user", "expansion"], expanded=True, depth=9) == expected_output


@pytest.mark.unit_test
def test_delete_xpansion_configuration(tmp_path: Path) -> None:
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
    "version, expected_output",
    [
        (
            720,
            {
                "additional-constraints": None,
                "ampl.presolve": 0,
                "ampl.solve_bounds_frequency": 1000000,
                "ampl.solver": "cbc",
                "batch_size": 0,
                "cut-type": CutType.YEARLY,
                "log_level": 0,
                "master": Master.INTEGER,
                "max_iteration": MaxIteration.INF,
                "optimality_gap": 1.0,
                "relative_gap": None,
                "relaxed-optimality-gap": 1000000.0,
                "sensitivity_config": {"capex": False, "epsilon": 10000.0, "projection": []},
                "separation_parameter": 0.5,
                "solver": None,
                "timelimit": 1000000000000,
                "uc_type": UcType.EXPANSION_FAST,
                "yearly-weights": None,
            },
        ),
        (
            810,
            {
                "additional-constraints": None,
                "ampl.presolve": None,
                "ampl.solve_bounds_frequency": None,
                "ampl.solver": None,
                "batch_size": 0,
                "cut-type": None,
                "log_level": 0,
                "master": Master.INTEGER,
                "max_iteration": MaxIteration.INF,
                "optimality_gap": 1.0,
                "relative_gap": 1e-12,
                "relaxed-optimality-gap": None,
                "sensitivity_config": {"capex": False, "epsilon": 10000.0, "projection": []},
                "separation_parameter": 0.5,
                "solver": Solver.CBC,
                "timelimit": 1000000000000,
                "uc_type": UcType.EXPANSION_FAST,
                "yearly-weights": None,
            },
        ),
    ],
)
@pytest.mark.unit_test
def test_get_xpansion_settings(tmp_path: Path, version: int, expected_output: JSON) -> None:
    """
    Test the retrieval of the xpansion settings.
    """

    empty_study = make_empty_study(tmp_path, version)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=version)
    xpansion_manager = make_xpansion_manager(empty_study)

    xpansion_manager.create_xpansion_configuration(study)

    actual = xpansion_manager.get_xpansion_settings(study)
    assert actual.dict(by_alias=True) == expected_output


@pytest.mark.unit_test
def test_xpansion_sensitivity_settings(tmp_path: Path) -> None:
    """
    Test that attribute projection in sensitivity_config is optional
    """

    empty_study = make_empty_study(tmp_path, 720)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=720)
    xpansion_manager = make_xpansion_manager(empty_study)

    xpansion_manager.create_xpansion_configuration(study)
    expected_settings = XpansionSettingsDTO.parse_obj(
        {
            "optimality_gap": 1,
            "max_iteration": "+Inf",
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
            "sensitivity_config": XpansionSensitivitySettingsDTO(epsilon=0.1, capex=False),
        }
    )
    xpansion_manager.update_xpansion_settings(study, expected_settings)
    assert xpansion_manager.get_xpansion_settings(study) == expected_settings


@pytest.mark.unit_test
def test_update_xpansion_settings(tmp_path: Path) -> None:
    """
    Test the retrieval of the xpansion settings.
    """

    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)

    xpansion_manager.create_xpansion_configuration(study)

    expected = {
        "optimality_gap": 4.0,
        "max_iteration": 123,
        "uc_type": UcType.EXPANSION_FAST,
        "master": Master.INTEGER,
        "yearly-weights": None,
        "additional-constraints": None,
        "relaxed-optimality-gap": "1.2%",
        "cut-type": None,
        "ampl.solver": None,
        "ampl.presolve": None,
        "ampl.solve_bounds_frequency": None,
        "relative_gap": 1e-12,
        "batch_size": 4,
        "separation_parameter": 0.5,
        "solver": Solver.CBC,
        "timelimit": 1000000000000,
        "log_level": 0,
        "sensitivity_config": {"epsilon": 10000.0, "projection": [], "capex": False},
    }

    new_settings = XpansionSettingsDTO(**expected)

    xpansion_manager.update_xpansion_settings(study, new_settings)

    actual = xpansion_manager.get_xpansion_settings(study)
    assert actual.dict(by_alias=True) == expected


@pytest.mark.unit_test
def test_add_candidate(tmp_path: Path) -> None:
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

    assert empty_study.tree.get(["user", "expansion", "candidates"]) == candidates

    xpansion_manager.add_candidate(study, new_candidate2)
    candidates["2"] = new_candidate2.dict(by_alias=True, exclude_none=True)

    assert empty_study.tree.get(["user", "expansion", "candidates"]) == candidates


@pytest.mark.unit_test
def test_get_candidate(tmp_path: Path) -> None:
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

    assert xpansion_manager.get_candidate(study, new_candidate.name) == new_candidate
    assert xpansion_manager.get_candidate(study, new_candidate2.name) == new_candidate2


@pytest.mark.unit_test
def test_get_candidates(tmp_path: Path) -> None:
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
def test_update_candidates(tmp_path: Path) -> None:
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
    xpansion_manager.update_candidate(study, new_candidate.name, new_candidate2)

    assert xpansion_manager.get_candidate(study, candidate_name=new_candidate.name) == new_candidate2


@pytest.mark.unit_test
def test_delete_candidate(tmp_path: Path) -> None:
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
def test_update_constraints(tmp_path: Path) -> None:
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    with pytest.raises(XpansionFileNotFoundError):
        xpansion_manager.update_xpansion_constraints_settings(study=study, constraints_file_name="non_existent_file")

    with pytest.raises(XpansionFileNotFoundError):
        xpansion_manager.update_xpansion_constraints_settings(study=study, constraints_file_name="non_existent_file")

    empty_study.tree.save({"user": {"expansion": {"constraints": {"constraints.txt": b"0"}}}})

    xpansion_manager.update_xpansion_constraints_settings(study=study, constraints_file_name="constraints.txt")

    assert xpansion_manager.get_xpansion_settings(study).additional_constraints == "constraints.txt"

    xpansion_manager.update_xpansion_constraints_settings(study=study, constraints_file_name=None)
    assert xpansion_manager.get_xpansion_settings(study).additional_constraints is None


@pytest.mark.unit_test
def test_add_resources(tmp_path: Path) -> None:
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "constraints1.txt"
    filename2 = "constraints2.txt"
    filename3 = "weight.txt"
    content1 = "0"
    content2 = "1"
    content3 = "2"

    upload_file_list = [
        UploadFile(filename=filename1, file=io.StringIO(content1)),
        UploadFile(filename=filename2, file=io.StringIO(content2)),
    ]

    xpansion_manager.add_resource(study, XpansionResourceFileType.CONSTRAINTS, upload_file_list)

    xpansion_manager.add_resource(
        study,
        XpansionResourceFileType.WEIGHTS,
        [UploadFile(filename=filename3, file=io.StringIO(content3))],
    )

    assert filename1 in empty_study.tree.get(["user", "expansion", "constraints"])
    expected1 = empty_study.tree.get(["user", "expansion", "constraints", filename1])
    assert content1.encode() == t.cast(bytes, expected1)

    assert filename2 in empty_study.tree.get(["user", "expansion", "constraints"])
    expected2 = empty_study.tree.get(["user", "expansion", "constraints", filename2])
    assert content2.encode() == t.cast(bytes, expected2)

    assert filename3 in empty_study.tree.get(["user", "expansion", "weights"])
    assert {
        "columns": [0],
        "data": [[2.0]],
        "index": [0],
    } == empty_study.tree.get(["user", "expansion", "weights", filename3])

    settings = xpansion_manager.get_xpansion_settings(study)
    settings.yearly_weights = filename3
    xpansion_manager.update_xpansion_settings(study, settings)
    with pytest.raises(FileCurrentlyUsedInSettings):
        xpansion_manager.delete_resource(study, XpansionResourceFileType.WEIGHTS, filename3)
    settings.yearly_weights = None
    xpansion_manager.update_xpansion_settings(study, settings)
    xpansion_manager.delete_resource(study, XpansionResourceFileType.WEIGHTS, filename3)


@pytest.mark.unit_test
def test_list_root_resources(tmp_path: Path) -> None:
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)
    constraints_file_content = b"0"
    constraints_file_name = "unknownfile.txt"

    empty_study.tree.save({"user": {"expansion": {constraints_file_name: constraints_file_content}}})
    assert [constraints_file_name] == xpansion_manager.list_root_files(study)


@pytest.mark.unit_test
def test_get_single_constraints(tmp_path: Path) -> None:
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    constraints_file_content = b"0"
    constraints_file_name = "constraints.txt"

    empty_study.tree.save({"user": {"expansion": {"constraints": {constraints_file_name: constraints_file_content}}}})

    assert (
        xpansion_manager.get_resource_content(study, XpansionResourceFileType.CONSTRAINTS, constraints_file_name)
        == constraints_file_content
    )


@pytest.mark.unit_test
def test_get_all_constraints(tmp_path: Path) -> None:
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "constraints1.txt"
    filename2 = "constraints2.txt"
    content1 = "0"
    content2 = "1"

    upload_file_list = [
        UploadFile(filename=filename1, file=io.StringIO(content1)),
        UploadFile(filename=filename2, file=io.StringIO(content2)),
    ]

    xpansion_manager.add_resource(study, XpansionResourceFileType.CONSTRAINTS, upload_file_list)

    assert xpansion_manager.list_resources(study, XpansionResourceFileType.CONSTRAINTS) == [
        filename1,
        filename2,
    ]


@pytest.mark.unit_test
def test_add_capa(tmp_path: Path) -> None:
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = "0"
    content2 = "1"

    upload_file_list = [
        UploadFile(filename=filename1, file=io.StringIO(content1)),
        UploadFile(filename=filename2, file=io.StringIO(content2)),
    ]

    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, upload_file_list)

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
def test_delete_capa(tmp_path: Path) -> None:
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = "0"
    content2 = "1"

    upload_file_list = [
        UploadFile(filename=filename1, file=io.StringIO(content1)),
        UploadFile(filename=filename2, file=io.StringIO(content2)),
    ]

    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, upload_file_list)

    xpansion_manager.delete_resource(study, XpansionResourceFileType.CAPACITIES, filename1)

    assert filename1 not in empty_study.tree.get(["user", "expansion", "capa"])

    assert filename2 in empty_study.tree.get(["user", "expansion", "capa"])


@pytest.mark.unit_test
def test_get_single_capa(tmp_path: Path) -> None:
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = "0"
    content2 = "3\nbc\td"

    upload_file_list = [
        UploadFile(filename=filename1, file=io.StringIO(content1)),
        UploadFile(filename=filename2, file=io.StringIO(content2)),
    ]

    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, upload_file_list)

    assert xpansion_manager.get_resource_content(study, XpansionResourceFileType.CAPACITIES, filename1) == {
        "columns": [0],
        "data": [[0.0]],
        "index": [0],
    }
    with pytest.raises(ParserError):
        xpansion_manager.get_resource_content(study, XpansionResourceFileType.CAPACITIES, filename2)


@pytest.mark.unit_test
def test_get_all_capa(tmp_path: Path) -> None:
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=empty_study.config.study_path, version=810)
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = "0"
    content2 = "1"

    upload_file_list = [
        UploadFile(filename=filename1, file=io.StringIO(content1)),
        UploadFile(filename=filename2, file=io.StringIO(content2)),
    ]

    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, upload_file_list)

    assert xpansion_manager.list_resources(study, XpansionResourceFileType.CAPACITIES) == [filename1, filename2]
