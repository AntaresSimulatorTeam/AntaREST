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

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.model import JSON
from antarest.study.business.xpansion_management import (
    FileCurrentlyUsedInSettings,
    LinkNotFound,
    Master,
    Solver,
    UcType,
    UpdateXpansionSettings,
    XpansionCandidateDTO,
    XpansionFileNotFoundError,
    XpansionManager,
    XpansionResourceFileType,
)
from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
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


def set_up_xpansion_manager(tmp_path: Path) -> t.Tuple[FileStudy, RawStudy, XpansionManager]:
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=str(empty_study.config.study_path), version="810")
    xpansion_manager = make_xpansion_manager(empty_study)
    xpansion_manager.create_xpansion_configuration(study)
    return empty_study, study, xpansion_manager


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "version, expected_output",
    [
        (
            810,
            {
                "candidates": {},
                "capa": {},
                "constraints": {},
                "sensitivity": {"sensitivity_in": {}},
                "settings": {
                    "master": "integer",
                    "uc_type": "expansion_fast",
                    "optimality_gap": 1,
                    "relative_gap": 1e-06,
                    "relaxed_optimality_gap": 1e-05,
                    "max_iteration": 1000,
                    "solver": "Xpress",
                    "log_level": 0,
                    "separation_parameter": 0.5,
                    "batch_size": 96,
                    "yearly-weights": "",
                    "additional-constraints": "",
                    "timelimit": int(1e12),
                },
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
    study = RawStudy(id="1", path=str(empty_study.config.study_path), version=str(version))
    xpansion_manager = make_xpansion_manager(empty_study)

    with pytest.raises(ChildNotFoundError):
        empty_study.tree.get(["user", "expansion"], depth=9, expanded=True)

    xpansion_manager.create_xpansion_configuration(study)

    actual = empty_study.tree.get(["user", "expansion"], depth=9, expanded=True)
    assert actual == expected_output


@pytest.mark.unit_test
def test_delete_xpansion_configuration(tmp_path: Path) -> None:
    """
    Test the deletion of a configuration.
    """
    empty_study = make_empty_study(tmp_path, 810)
    study = RawStudy(id="1", path=str(empty_study.config.study_path), version="810")
    xpansion_manager = make_xpansion_manager(empty_study)

    with pytest.raises(ChildNotFoundError):
        empty_study.tree.get(["user", "expansion"], depth=9, expanded=True)

    xpansion_manager.create_xpansion_configuration(study)

    assert empty_study.tree.get(["user", "expansion"], depth=9, expanded=True)

    xpansion_manager.delete_xpansion_configuration(study)

    with pytest.raises(ChildNotFoundError):
        empty_study.tree.get(["user", "expansion"], depth=9, expanded=True)


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "version, expected_output",
    [
        (
            810,
            {
                "master": Master.INTEGER,
                "uc_type": UcType.EXPANSION_FAST,
                "optimality_gap": 1.0,
                "relative_gap": 1e-06,
                "relaxed_optimality_gap": 1e-05,
                "max_iteration": 1000,
                "solver": Solver.XPRESS,
                "log_level": 0,
                "separation_parameter": 0.5,
                "batch_size": 96,
                "yearly-weights": "",
                "additional-constraints": "",
                "timelimit": int(1e12),
                "sensitivity_config": {"epsilon": 0, "projection": [], "capex": False},
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
    study = RawStudy(id="1", path=str(empty_study.config.study_path), version=str(version))
    xpansion_manager = make_xpansion_manager(empty_study)

    xpansion_manager.create_xpansion_configuration(study)

    actual = xpansion_manager.get_xpansion_settings(study)
    assert actual.dict(by_alias=True) == expected_output


@pytest.mark.unit_test
def test_update_xpansion_settings(tmp_path: Path) -> None:
    """
    Test the retrieval of the xpansion settings.
    """
    _, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

    new_settings_obj = {
        "optimality_gap": 4.0,
        "max_iteration": 123,
        "uc_type": UcType.EXPANSION_FAST,
        "master": Master.INTEGER,
        "yearly-weights": "",
        "additional-constraints": "",
        "relaxed_optimality_gap": "1.2%",  # percentage
        "relative_gap": 1e-12,
        "batch_size": 4,
        "separation_parameter": 0.5,
        "solver": Solver.CBC,
        "timelimit": int(1e12),
        "log_level": 0,
        "sensitivity_config": {"epsilon": 10500.0, "projection": ["foo"], "capex": False},
    }

    new_settings = UpdateXpansionSettings(**new_settings_obj)

    actual = xpansion_manager.update_xpansion_settings(study, new_settings)

    expected = {
        "master": Master.INTEGER,
        "uc_type": UcType.EXPANSION_FAST,
        "optimality_gap": 4.0,
        "relative_gap": 1e-12,
        "relaxed_optimality_gap": 1.2,
        "max_iteration": 123,
        "solver": Solver.CBC,
        "log_level": 0,
        "separation_parameter": 0.5,
        "batch_size": 4,
        "yearly-weights": "",
        "additional-constraints": "",
        "timelimit": int(1e12),
        "sensitivity_config": {"epsilon": 10500.0, "projection": ["foo"], "capex": False},
    }
    assert actual.dict(by_alias=True) == expected


@pytest.mark.unit_test
def test_add_candidate(tmp_path: Path) -> None:
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

    actual = empty_study.tree.get(["user", "expansion", "candidates"])
    assert actual == {}

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

    actual = empty_study.tree.get(["user", "expansion", "candidates"])
    assert actual == candidates

    xpansion_manager.add_candidate(study, new_candidate2)
    candidates["2"] = new_candidate2.dict(by_alias=True, exclude_none=True)

    actual = empty_study.tree.get(["user", "expansion", "candidates"])
    assert actual == candidates


@pytest.mark.unit_test
def test_get_candidate(tmp_path: Path) -> None:
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

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
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

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
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

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
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

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
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

    with pytest.raises(XpansionFileNotFoundError):
        xpansion_manager.update_xpansion_constraints_settings(study=study, constraints_file_name="non_existent_file")

    with pytest.raises(XpansionFileNotFoundError):
        xpansion_manager.update_xpansion_constraints_settings(study=study, constraints_file_name="non_existent_file")

    empty_study.tree.save({"user": {"expansion": {"constraints": {"constraints.txt": b"0"}}}})

    actual_settings = xpansion_manager.update_xpansion_constraints_settings(study, "constraints.txt")
    assert actual_settings.additional_constraints == "constraints.txt"

    actual_settings = xpansion_manager.update_xpansion_constraints_settings(study, "")
    assert actual_settings.additional_constraints == ""


@pytest.mark.unit_test
def test_add_resources(tmp_path: Path) -> None:
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

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

    assert filename1 in empty_study.tree.get(url=["user", "expansion", "constraints"], format="json")
    expected1 = empty_study.tree.get(url=["user", "expansion", "constraints", filename1], format="json")
    assert content1.encode() == t.cast(bytes, expected1)

    assert filename2 in empty_study.tree.get(url=["user", "expansion", "constraints"], format="json")
    expected2 = empty_study.tree.get(url=["user", "expansion", "constraints", filename2], format="json")
    assert content2.encode() == t.cast(bytes, expected2)

    assert filename3 in empty_study.tree.get(url=["user", "expansion", "weights"], format="json")
    assert {
        "columns": [0],
        "data": [[2.0]],
        "index": [0],
    } == empty_study.tree.get(url=["user", "expansion", "weights", filename3], format="json")

    settings = xpansion_manager.get_xpansion_settings(study)
    settings.yearly_weights = filename3
    update_settings = UpdateXpansionSettings(**settings.dict())
    xpansion_manager.update_xpansion_settings(study, update_settings)

    with pytest.raises(FileCurrentlyUsedInSettings):
        xpansion_manager.delete_resource(study, XpansionResourceFileType.WEIGHTS, filename3)

    settings.yearly_weights = ""
    update_settings = UpdateXpansionSettings(**settings.dict())
    xpansion_manager.update_xpansion_settings(study, update_settings)
    xpansion_manager.delete_resource(study, XpansionResourceFileType.WEIGHTS, filename3)


@pytest.mark.unit_test
def test_list_root_resources(tmp_path: Path) -> None:
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

    constraints_file_content = b"0"
    constraints_file_name = "unknownfile.txt"

    empty_study.tree.save({"user": {"expansion": {constraints_file_name: constraints_file_content}}})
    assert [constraints_file_name] == xpansion_manager.list_root_files(study)


@pytest.mark.unit_test
def test_get_single_constraints(tmp_path: Path) -> None:
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

    constraints_file_content = b"0"
    constraints_file_name = "constraints.txt"

    empty_study.tree.save({"user": {"expansion": {"constraints": {constraints_file_name: constraints_file_content}}}})

    assert (
        xpansion_manager.get_resource_content(study, XpansionResourceFileType.CONSTRAINTS, constraints_file_name)
        == constraints_file_content
    )


@pytest.mark.unit_test
def test_get_settings_without_sensitivity(tmp_path: Path) -> None:
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

    empty_study.tree.delete(["user", "expansion", "sensitivity"])
    # should not fail even if the folder doesn't exist as it's optional
    xpansion_manager.get_xpansion_settings(study)


@pytest.mark.unit_test
def test_get_all_constraints(tmp_path: Path) -> None:
    _, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

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
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = "0"
    content2 = "1"

    upload_file_list = [
        UploadFile(filename=filename1, file=io.StringIO(content1)),
        UploadFile(filename=filename2, file=io.StringIO(content2)),
    ]

    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, upload_file_list)

    assert filename1 in empty_study.tree.get(url=["user", "expansion", "capa"], format="json")
    assert {
        "columns": [0],
        "data": [[0.0]],
        "index": [0],
    } == empty_study.tree.get(url=["user", "expansion", "capa", filename1], format="json")

    assert filename2 in empty_study.tree.get(url=["user", "expansion", "capa"], format="json")
    assert {
        "columns": [0],
        "data": [[1.0]],
        "index": [0],
    } == empty_study.tree.get(url=["user", "expansion", "capa", filename2], format="json")


@pytest.mark.unit_test
def test_delete_capa(tmp_path: Path) -> None:
    empty_study, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

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
    _, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

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
    _, study, xpansion_manager = set_up_xpansion_manager(tmp_path)

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
