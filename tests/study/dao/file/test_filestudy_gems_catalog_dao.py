# Copyright (c) 2026, RTE (https://www.rte-france.com)
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


from pathlib import Path

import pytest

from antarest.core.exceptions import GemsCatalogAlreadyExists
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.gems.catalog import GemsCatalog
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.dao.api.study_dao import ReadOnlyAdapter, StudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.dao.study_conversion.study_converter import StudyConverter
from antarest.study.model import STUDY_VERSION_10_2
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader

ASSET = Path(__file__).parent.parent / "assets/gems/catalogs/antares_legacy_area_catalog.yml"


@pytest.mark.parametrize("suffix", [".yml", ".yaml"])
def test_real_file_roundtrip(filestudy_dao_v10_2: FileStudyTreeDao, gems_catalog: GemsCatalog, suffix: str) -> None:
    dao = filestudy_dao_v10_2
    folder = dao.get_file_study().config.study_path / "input/catalogs"
    folder.mkdir(parents=True)
    source = folder / f"unrelated_filename{suffix}"
    source.write_bytes(ASSET.read_bytes())
    (folder / "README.txt").write_text("Ignored")
    (folder / "subdirectory.yaml").mkdir()
    assert dao.get_catalogs() == [gems_catalog]

    # Check IDs inside documents, even if their filenames are different.
    with pytest.raises(GemsCatalogAlreadyExists):
        dao.save_catalog(gems_catalog)
    source.unlink()
    dao.save_catalog(gems_catalog)
    assert YAMLReader().read(folder / f"{gems_catalog.id}.yaml") == YAMLReader().read(ASSET)


def test_duplicate_ids(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    folder = filestudy_dao_v10_2.get_file_study().config.study_path / "input/catalogs"
    folder.mkdir(parents=True)
    (folder / "first.yml").write_bytes(ASSET.read_bytes())
    (folder / "second.yaml").write_bytes(ASSET.read_bytes())
    with pytest.raises(GemsCatalogAlreadyExists):
        filestudy_dao_v10_2.get_catalogs()


def test_filename_collision_does_not_overwrite(
    filestudy_dao_v10_2: FileStudyTreeDao, gems_catalog: GemsCatalog
) -> None:
    dao = filestudy_dao_v10_2
    folder = dao.get_file_study().config.study_path / "input/catalogs"
    folder.mkdir(parents=True)
    existing = folder / "another_catalog.yaml"
    existing.write_bytes(ASSET.read_bytes())
    with pytest.raises(GemsCatalogAlreadyExists):
        dao.save_catalog(gems_catalog.model_copy(update={"id": "another_catalog"}))
    assert existing.read_bytes() == ASSET.read_bytes()


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
@pytest.mark.parametrize("with_catalogs", [False, True])
def test_conversion_roundtrip(
    dao_10_2: StudyDao,
    filestudy_dao_v10_2: FileStudyTreeDao,
    matrix_service: ISimpleMatrixService,
    gems_catalog: GemsCatalog,
    with_catalogs: bool,
) -> None:
    file_dao = filestudy_dao_v10_2
    file_dao.save_library(GemsLibrary(id="test_library"))
    expected = []
    if with_catalogs:
        expected = [gems_catalog, gems_catalog.model_copy(update={"id": "second_catalog"})]
        for catalog in expected:
            file_dao.save_catalog(catalog)

    # Exercise the full import, including the read-only adapter used by callers.
    StudyConverter(ReadOnlyAdapter(file_dao), dao_10_2, STUDY_VERSION_10_2, matrix_service).convert_study_inputs()
    assert dao_10_2.get_catalogs() == expected
    study_path = file_dao.get_file_study().config.study_path
    for path in (study_path / "input/catalogs").glob("*.yaml"):
        path.unlink()
    (study_path / "input/model-libraries/library.yaml").unlink()
    # The destination already contains the legacy inputs, only copy GEMS back.
    StudyConverter(dao_10_2, file_dao, STUDY_VERSION_10_2, matrix_service)._convert_gems()
    assert file_dao.get_catalogs() == expected
    if with_catalogs:
        assert YAMLReader().read(study_path / f"input/catalogs/{gems_catalog.id}.yaml") == YAMLReader().read(ASSET)
