# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import io
from pathlib import Path

import pytest
from fastapi import UploadFile

from antarest.core.exceptions import (
    AreaNotFound,
    ChildNotFoundError,
    FileCurrentlyUsedInSettings,
    LinkNotFound,
    MatrixImportFailed,
    XpansionFileNotFoundError,
)
from antarest.study.business.area_management import AreaManager
from antarest.study.business.link_management import LinkManager
from antarest.study.business.model.area_model import AreaCreationDTO, AreaType
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.xpansion_model import (
    Master,
    Solver,
    UcType,
    XpansionResourceFileType,
    XpansionSettingsUpdate,
)
from antarest.study.business.study_interface import FileStudyInterface, StudyInterface
from antarest.study.business.xpansion_management import (
    XpansionCandidateDTO,
    XpansionManager,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


def make_areas(area_manager: AreaManager, study: StudyInterface) -> None:
    area_manager.create_area(study, AreaCreationDTO(type=AreaType.AREA, name="area1"))
    area_manager.create_area(study, AreaCreationDTO(type=AreaType.AREA, name="area2"))


def make_link(link_manager: LinkManager, study: StudyInterface) -> None:
    link_manager.create_link(study, Link(area1="area1", area2="area2"))


@pytest.mark.unit_test
def test_create_configuration(
    xpansion_manager: XpansionManager,
    tmp_path: Path,
    empty_study_810: FileStudy,
) -> None:
    """
    Test the creation of a configuration.
    """
    study = FileStudyInterface(empty_study_810)
    with pytest.raises(ChildNotFoundError):
        study.get_files().tree.get(["user", "expansion"], expanded=True, depth=9)

    xpansion_manager.create_xpansion_configuration(study)

    actual = study.get_files().tree.get(["user", "expansion"], expanded=True, depth=9)
    assert actual == {
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
            "timelimit": int(1e12),
        },
        "weights": {},
    }


@pytest.mark.unit_test
def test_delete_xpansion_configuration(
    xpansion_manager: XpansionManager, tmp_path: Path, empty_study_810: FileStudy
) -> None:
    """
    Test the deletion of a configuration.
    """
    study = FileStudyInterface(empty_study_810)
    with pytest.raises(ChildNotFoundError):
        study.get_files().tree.get(["user", "expansion"], expanded=True, depth=9)

    xpansion_manager.create_xpansion_configuration(study)

    assert study.get_files().tree.get(["user", "expansion"], expanded=True, depth=9)

    xpansion_manager.delete_xpansion_configuration(study)

    with pytest.raises(ChildNotFoundError):
        study.get_files().tree.get(["user", "expansion"], expanded=True, depth=9)


@pytest.mark.unit_test
def test_get_xpansion_settings(xpansion_manager: XpansionManager, tmp_path: Path, empty_study_810: FileStudy) -> None:
    """
    Test the retrieval of the xpansion settings.
    """
    study = FileStudyInterface(empty_study_810)
    xpansion_manager.create_xpansion_configuration(study)

    actual = xpansion_manager.get_xpansion_settings(study)
    assert actual.model_dump(by_alias=True) == {
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
    }


@pytest.mark.unit_test
def test_update_xpansion_settings(xpansion_manager: XpansionManager, empty_study_810: FileStudy) -> None:
    """
    Test the retrieval of the xpansion settings.
    """
    study = FileStudyInterface(empty_study_810)
    xpansion_manager.create_xpansion_configuration(study)

    new_settings_obj = {
        "optimality_gap": 4.0,
        "max_iteration": 123,
        "uc_type": UcType.EXPANSION_FAST,
        "master": Master.INTEGER,
        "relaxed_optimality_gap": "1.2%",  # percentage
        "relative_gap": 1e-12,
        "batch_size": 4,
        "separation_parameter": 0.5,
        "solver": Solver.CBC,
        "timelimit": int(1e12),
        "log_level": 0,
        "sensitivity_config": {"epsilon": 10500.0, "projection": ["foo"], "capex": False},
    }

    new_settings = XpansionSettingsUpdate(**new_settings_obj)

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
    assert actual.model_dump(by_alias=True) == expected


@pytest.mark.unit_test
def test_add_candidate(
    link_manager: LinkManager,
    area_manager: AreaManager,
    xpansion_manager: XpansionManager,
    empty_study_810: FileStudy,
) -> None:
    study = FileStudyInterface(empty_study_810)
    xpansion_manager.create_xpansion_configuration(study)

    actual = study.get_files().tree.get(["user", "expansion", "candidates"])
    assert actual == {}

    new_candidate = XpansionCandidateDTO.model_validate(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    new_candidate2 = XpansionCandidateDTO.model_validate(
        {
            "name": "candidate_2",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    with pytest.raises(AreaNotFound, match="Area is not found: 'area1'"):
        xpansion_manager.add_candidate(study, new_candidate)

    make_areas(area_manager, study)

    with pytest.raises(LinkNotFound, match="The link from 'area1' to 'area2' not found"):
        xpansion_manager.add_candidate(study, new_candidate)

    make_link(link_manager, study)

    xpansion_manager.add_candidate(study, new_candidate)

    candidates = {"1": new_candidate.model_dump(by_alias=True, exclude_none=True)}

    actual = study.get_files().tree.get(["user", "expansion", "candidates"])
    assert actual == candidates

    xpansion_manager.add_candidate(study, new_candidate2)
    candidates["2"] = new_candidate2.model_dump(by_alias=True, exclude_none=True)

    actual = study.get_files().tree.get(["user", "expansion", "candidates"])
    assert actual == candidates


@pytest.mark.unit_test
def test_get_candidate(
    link_manager: LinkManager,
    area_manager: AreaManager,
    xpansion_manager: XpansionManager,
    empty_study_810: FileStudy,
) -> None:
    study = FileStudyInterface(empty_study_810)
    xpansion_manager.create_xpansion_configuration(study)
    make_areas(area_manager, study)
    make_link(link_manager, study)

    assert study.get_files().tree.get(["user", "expansion", "candidates"]) == {}

    new_candidate = XpansionCandidateDTO.model_validate(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    new_candidate2 = XpansionCandidateDTO.model_validate(
        {
            "name": "candidate_2",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    xpansion_manager.add_candidate(study, new_candidate)
    xpansion_manager.add_candidate(study, new_candidate2)

    assert xpansion_manager.get_candidate(study, new_candidate.name) == new_candidate
    assert xpansion_manager.get_candidate(study, new_candidate2.name) == new_candidate2


@pytest.mark.unit_test
def test_get_candidates(
    link_manager: LinkManager,
    area_manager: AreaManager,
    xpansion_manager: XpansionManager,
    empty_study_810: FileStudy,
) -> None:
    study = FileStudyInterface(empty_study_810)
    xpansion_manager.create_xpansion_configuration(study)
    make_areas(area_manager, study)
    make_link(link_manager, study)

    assert study.get_files().tree.get(["user", "expansion", "candidates"]) == {}

    new_candidate = XpansionCandidateDTO.model_validate(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    new_candidate2 = XpansionCandidateDTO.model_validate(
        {
            "name": "candidate_2",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )

    xpansion_manager.add_candidate(study, new_candidate)
    xpansion_manager.add_candidate(study, new_candidate2)

    assert xpansion_manager.get_candidates(study) == [
        new_candidate,
        new_candidate2,
    ]


@pytest.mark.unit_test
def test_update_candidates(
    link_manager: LinkManager,
    area_manager: AreaManager,
    xpansion_manager: XpansionManager,
    empty_study_810: FileStudy,
) -> None:
    study = FileStudyInterface(empty_study_810)
    xpansion_manager.create_xpansion_configuration(study)
    make_areas(area_manager, study)
    make_link(link_manager, study)

    assert study.get_files().tree.get(["user", "expansion", "candidates"]) == {}

    new_candidate = XpansionCandidateDTO.model_validate(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )
    xpansion_manager.add_candidate(study, new_candidate)

    new_candidate2 = XpansionCandidateDTO.model_validate(
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
def test_delete_candidate(
    link_manager: LinkManager,
    area_manager: AreaManager,
    xpansion_manager: XpansionManager,
    empty_study_810: FileStudy,
) -> None:
    study = FileStudyInterface(empty_study_810)
    xpansion_manager.create_xpansion_configuration(study)
    make_areas(area_manager, study)
    make_link(link_manager, study)

    assert study.get_files().tree.get(["user", "expansion", "candidates"]) == {}

    new_candidate = XpansionCandidateDTO.model_validate(
        {
            "name": "candidate_1",
            "link": "area1 - area2",
            "annual-cost-per-mw": 1,
            "max-investment": 1,
        }
    )
    xpansion_manager.add_candidate(study, new_candidate)

    new_candidate2 = XpansionCandidateDTO.model_validate(
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
def test_update_constraints(
    xpansion_manager: XpansionManager,
    empty_study_810: FileStudy,
) -> None:
    study = FileStudyInterface(empty_study_810)
    xpansion_manager.create_xpansion_configuration(study)

    with pytest.raises(
        XpansionFileNotFoundError, match="Additional constraints file 'non_existent_file' does not exist"
    ):
        xpansion_manager.update_xpansion_constraints_settings(study=study, constraints_file_name="non_existent_file")

    study.get_files().tree.save({"user": {"expansion": {"constraints": {"constraints.txt": b"0"}}}})

    actual_settings = xpansion_manager.update_xpansion_constraints_settings(study, "constraints.txt")
    assert actual_settings.additional_constraints == "constraints.txt"

    actual_settings = xpansion_manager.update_xpansion_constraints_settings(study, "")
    assert actual_settings.additional_constraints == ""


@pytest.mark.unit_test
def test_update_constraints_via_the_front(
    xpansion_manager: XpansionManager,
    empty_study_880: FileStudy,
) -> None:
    study = FileStudyInterface(empty_study_880)
    xpansion_manager.create_xpansion_configuration(study)

    study.get_files().tree.save({"user": {"expansion": {"constraints": {"constraints.txt": b"0"}}}})

    # asserts we can update a field without writing the field additional constraint in the file
    front_settings = XpansionSettingsUpdate(master="relaxed")
    xpansion_manager.update_xpansion_settings(study, front_settings)
    json_content = study.get_files().tree.get(["user", "expansion", "settings"])
    assert "additional-constraints" not in json_content
    assert json_content["master"] == "relaxed"

    # asserts the front-end can fill additional constraints
    new_constraint = {"additional-constraints": "constraints.txt"}
    front_settings = XpansionSettingsUpdate.model_validate(new_constraint)
    actual_settings = xpansion_manager.update_xpansion_settings(study, front_settings)
    assert actual_settings.additional_constraints == "constraints.txt"
    json_content = study.get_files().tree.get(["user", "expansion", "settings"])
    assert json_content["additional-constraints"] == "constraints.txt"

    # asserts the front-end can unselect this constraint by not filling it
    front_settings = XpansionSettingsUpdate()
    actual_settings = xpansion_manager.update_xpansion_settings(study, front_settings)
    assert actual_settings.additional_constraints == ""
    json_content = study.get_files().tree.get(["user", "expansion", "settings"])
    assert "additional-constraints" not in json_content


@pytest.mark.unit_test
def test_update_weights_via_the_front(
    xpansion_manager: XpansionManager,
    empty_study_880: FileStudy,
) -> None:
    study = FileStudyInterface(empty_study_880)
    xpansion_manager.create_xpansion_configuration(study)
    # Same test as the one for constraints
    study.get_files().tree.save({"user": {"expansion": {"weights": {"weights.txt": b"0"}}}})

    # asserts we can update a field without writing the field yearly-weights in the file
    front_settings = XpansionSettingsUpdate(master="relaxed")
    xpansion_manager.update_xpansion_settings(study, front_settings)
    json_content = study.get_files().tree.get(["user", "expansion", "settings"])
    assert "yearly-weights" not in json_content
    assert json_content["master"] == "relaxed"

    # asserts the front-end can fill yearly weights
    new_constraint = {"yearly-weights": "weights.txt"}
    front_settings = XpansionSettingsUpdate.model_validate(new_constraint)
    actual_settings = xpansion_manager.update_xpansion_settings(study, front_settings)
    assert actual_settings.yearly_weights == "weights.txt"
    json_content = study.get_files().tree.get(["user", "expansion", "settings"])
    assert json_content["yearly-weights"] == "weights.txt"

    # asserts the front-end can unselect this weight by not filling it
    front_settings = XpansionSettingsUpdate()
    actual_settings = xpansion_manager.update_xpansion_settings(study, front_settings)
    assert actual_settings.yearly_weights == ""
    json_content = study.get_files().tree.get(["user", "expansion", "settings"])
    assert "yearly-weights" not in json_content


@pytest.mark.unit_test
def test_add_resources(
    xpansion_manager: XpansionManager,
    study: StudyInterface,
) -> None:
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "constraints1.txt"
    filename2 = "constraints2.txt"
    filename3 = "weight.txt"
    content1 = b"0"
    content2 = b"1"
    content3 = b"2"

    file_1 = UploadFile(filename=filename1, file=io.BytesIO(content1))
    file_2 = UploadFile(filename=filename2, file=io.BytesIO(content2))
    file_3 = UploadFile(filename=filename3, file=io.BytesIO(content3))

    xpansion_manager.add_resource(study, XpansionResourceFileType.CONSTRAINTS, file_1)
    xpansion_manager.add_resource(study, XpansionResourceFileType.CONSTRAINTS, file_2)
    xpansion_manager.add_resource(study, XpansionResourceFileType.WEIGHTS, file_3)

    assert filename1 in study.get_files().tree.get(["user", "expansion", "constraints"])
    expected1 = study.get_files().tree.get(["user", "expansion", "constraints", filename1])
    assert content1 == expected1

    assert filename2 in study.get_files().tree.get(["user", "expansion", "constraints"])
    expected2 = study.get_files().tree.get(["user", "expansion", "constraints", filename2])
    assert content2 == expected2

    assert filename3 in study.get_files().tree.get(["user", "expansion", "weights"])
    assert {
        "columns": [0],
        "data": [[2.0]],
        "index": [0],
    } == study.get_files().tree.get(["user", "expansion", "weights", filename3])

    settings = xpansion_manager.get_xpansion_settings(study)
    settings.yearly_weights = filename3
    update_settings = XpansionSettingsUpdate(**settings.model_dump())
    xpansion_manager.update_xpansion_settings(study, update_settings)

    with pytest.raises(
        FileCurrentlyUsedInSettings,
        match=f"The weights file '{filename3}' is still used in the xpansion settings and cannot be deleted",
    ):
        xpansion_manager.delete_resource(study, XpansionResourceFileType.WEIGHTS, filename3)

    settings.yearly_weights = ""
    update_settings = XpansionSettingsUpdate(**settings.model_dump())
    xpansion_manager.update_xpansion_settings(study, update_settings)
    xpansion_manager.delete_resource(study, XpansionResourceFileType.WEIGHTS, filename3)


@pytest.mark.unit_test
def test_get_single_constraints(
    xpansion_manager: XpansionManager,
    empty_study_870: FileStudy,
) -> None:
    study = FileStudyInterface(empty_study_870)
    xpansion_manager.create_xpansion_configuration(study)

    constraints_file_content = b"0"
    constraints_file_name = "constraints.txt"

    study.get_files().tree.save(
        {"user": {"expansion": {"constraints": {constraints_file_name: constraints_file_content}}}}
    )

    assert (
        xpansion_manager.get_resource_content(study, XpansionResourceFileType.CONSTRAINTS, constraints_file_name)
        == constraints_file_content
    )


@pytest.mark.unit_test
def test_get_settings_without_sensitivity(
    xpansion_manager: XpansionManager,
    empty_study_870: FileStudy,
) -> None:
    study = FileStudyInterface(empty_study_870)
    xpansion_manager.create_xpansion_configuration(study)

    study.get_files().tree.delete(["user", "expansion", "sensitivity"])
    # should not fail even if the folder doesn't exist as it's optional
    xpansion_manager.get_xpansion_settings(study)


@pytest.mark.unit_test
def test_get_all_constraints(
    xpansion_manager: XpansionManager,
    study: StudyInterface,
) -> None:
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "constraints1.txt"
    filename2 = "constraints2.txt"
    content1 = b"0"
    content2 = b"1"

    file_1 = UploadFile(filename=filename1, file=io.BytesIO(content1))
    file_2 = UploadFile(filename=filename2, file=io.BytesIO(content2))

    xpansion_manager.add_resource(study, XpansionResourceFileType.CONSTRAINTS, file_1)
    xpansion_manager.add_resource(study, XpansionResourceFileType.CONSTRAINTS, file_2)

    assert xpansion_manager.list_resources(study, XpansionResourceFileType.CONSTRAINTS) == [
        filename1,
        filename2,
    ]


@pytest.mark.unit_test
def test_add_capa(
    xpansion_manager: XpansionManager,
    study: StudyInterface,
) -> None:
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = b"0"
    content2 = b"1"

    file_1 = UploadFile(filename=filename1, file=io.BytesIO(content1))
    file_2 = UploadFile(filename=filename2, file=io.BytesIO(content2))

    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, file_1)
    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, file_2)

    assert filename1 in study.get_files().tree.get(["user", "expansion", "capa"])
    assert {
        "columns": [0],
        "data": [[0.0]],
        "index": [0],
    } == study.get_files().tree.get(["user", "expansion", "capa", filename1])

    assert filename2 in study.get_files().tree.get(["user", "expansion", "capa"])
    assert {
        "columns": [0],
        "data": [[1.0]],
        "index": [0],
    } == study.get_files().tree.get(["user", "expansion", "capa", filename2])


@pytest.mark.unit_test
def test_delete_capa(
    xpansion_manager: XpansionManager,
    study: StudyInterface,
) -> None:
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = b"0"
    content2 = b"1"

    file_1 = UploadFile(filename=filename1, file=io.BytesIO(content1))
    file_2 = UploadFile(filename=filename2, file=io.BytesIO(content2))

    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, file_1)
    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, file_2)

    xpansion_manager.delete_resource(study, XpansionResourceFileType.CAPACITIES, filename1)

    assert filename1 not in study.get_files().tree.get(["user", "expansion", "capa"])

    assert filename2 in study.get_files().tree.get(["user", "expansion", "capa"])


@pytest.mark.unit_test
def test_get_single_capa(
    xpansion_manager: XpansionManager,
    study: StudyInterface,
) -> None:
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = b"0"
    content2 = b"3\nbc\td"

    file_1 = UploadFile(filename=filename1, file=io.BytesIO(content1))
    file_2 = UploadFile(filename=filename2, file=io.BytesIO(content2))

    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, file_1)

    assert xpansion_manager.get_resource_content(study, XpansionResourceFileType.CAPACITIES, filename1) == {
        "columns": [0],
        "data": [[0.0]],
        "index": [0],
    }
    with pytest.raises(MatrixImportFailed):
        xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, file_2)


@pytest.mark.unit_test
def test_get_all_capa(
    xpansion_manager: XpansionManager,
    study: StudyInterface,
) -> None:
    xpansion_manager.create_xpansion_configuration(study)

    filename1 = "capa1.txt"
    filename2 = "capa2.txt"
    content1 = b"0"
    content2 = b"1"

    file_1 = UploadFile(filename=filename1, file=io.BytesIO(content1))
    file_2 = UploadFile(filename=filename2, file=io.BytesIO(content2))

    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, file_1)
    xpansion_manager.add_resource(study, XpansionResourceFileType.CAPACITIES, file_2)

    assert xpansion_manager.list_resources(study, XpansionResourceFileType.CAPACITIES) == [filename1, filename2]
