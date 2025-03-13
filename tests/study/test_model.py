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

"""
Test the database model.
"""

import uuid

from sqlalchemy import inspect 
from sqlalchemy.engine import Engine 
from sqlalchemy.orm import Session, joinedload 

from antarest.study.model import Study, StudyTag, Tag


class TestStudy:
    """
    Test the study model.
    """

    def test_study(self, db_session: Session) -> None:
        """
        Basic test of the `study` table.
        """
        study_id = uuid.uuid4()

        with db_session:
            db_session.add(Study(id=str(study_id), name="Study 1"))
            db_session.commit()

        with db_session:
            study = db_session.query(Study).first()
            assert study.id == str(study_id)
            assert study.name == "Study 1"

    def test_index_on_study(self, db_engine: Engine) -> None:
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("study")
        index_names = {index["name"] for index in indexes}
        assert index_names == {
            "ix_study_archived",
            "ix_study_created_at",
            "ix_study_folder",
            "ix_study_name",
            "ix_study_owner_id",
            "ix_study_parent_id",
            "ix_study_type",
            "ix_study_updated_at",
            "ix_study_version",
        }

    def test_index_on_rawstudy(self, db_engine: Engine) -> None:
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("rawstudy")
        index_names = {index["name"] for index in indexes}
        assert index_names == {"ix_rawstudy_workspace", "ix_rawstudy_missing"}

    def test_index_on_variantstudy(self, db_engine: Engine) -> None:
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("variantstudy")
        index_names = {index["name"] for index in indexes}
        assert not index_names

    def test_index_on_study_additional_data(self, db_engine: Engine) -> None:
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("study_additional_data")
        index_names = {index["name"] for index in indexes}
        assert index_names == {"ix_study_additional_data_patch"}

    def test_study_tag_relationship(self, db_session: Session) -> None:
        study_id_1 = str(uuid.uuid4())
        study_id_2 = str(uuid.uuid4())
        study_id_3 = str(uuid.uuid4())

        with db_session:
            tag1 = Tag(label="test-tag-1")
            tag2 = Tag(label="test-tag-2")
            db_session.add(Study(id=study_id_1, name="TestStudyTags1", tags=[tag1, tag2]))
            db_session.add(Study(id=study_id_2, name="TestStudyTags2", tags=[tag1]))
            db_session.add(Study(id=study_id_3, name="TestStudyTags3"))
            db_session.commit()

            # verify that when the Study is initialized with tags so would the tables `tag` and `study_tag` be updated
            study_tag_pairs = db_session.query(StudyTag).all()
            tags = db_session.query(Tag).all()
            studies = db_session.query(Study).all()
            assert len(study_tag_pairs) == 3
            assert set(e.tag_label for e in study_tag_pairs) == {"test-tag-1", "test-tag-2"}
            assert set(e.study_id for e in study_tag_pairs) == {study_id_1, study_id_2}
            assert len(tags) == 2
            assert set(tag.label for tag in tags) == {"test-tag-1", "test-tag-2"}
            assert len(studies) == 3
            assert set(study.id for study in studies) == {study_id_1, study_id_2, study_id_3}

            # verify that ondelete works for studies
            db_session.query(Study).filter(Study.id == study_id_2).delete()
            db_session.commit()
            study_tag_pairs = db_session.query(StudyTag).all()
            tags = db_session.query(Tag).all()
            studies = db_session.query(Study).all()
            assert len(study_tag_pairs) == 2
            assert set(e.tag_label for e in study_tag_pairs) == {"test-tag-1", "test-tag-2"}
            assert set(e.study_id for e in study_tag_pairs) == {study_id_1}
            assert len(tags) == 2
            assert set(tag.label for tag in tags) == {"test-tag-1", "test-tag-2"}
            assert len(studies) == 2
            assert set(study.id for study in studies) == {study_id_1, study_id_3}

            # verify ondelete works for tags
            db_session.query(Tag).filter(Tag.label == "test-tag-2").delete()
            db_session.commit()
            study_tag_pairs = db_session.query(StudyTag).all()
            tags = db_session.query(Tag).all()
            studies = db_session.query(Study).all()
            assert len(study_tag_pairs) == 1
            assert set(e.tag_label for e in study_tag_pairs) == {"test-tag-1"}
            assert set(e.study_id for e in study_tag_pairs) == {study_id_1}
            assert len(tags) == 1
            assert set(tag.label for tag in tags) == {"test-tag-1"}
            assert len(studies) == 2
            assert set(study.id for study in studies) == {study_id_1, study_id_3}
            studies = db_session.query(Study).filter(Study.id == study_id_1).options(joinedload(Study.tags)).all()
            assert len(studies) == 1
            assert set(study.id for study in studies) == {study_id_1}
            assert set(tag.label for tag in studies[0].tags) == {"test-tag-1"}

            # verify updating works
            study = db_session.query(Study).get(study_id_1)
            study.tags = [Tag(label="test-tag-2"), Tag(label="test-tag-3")]
            db_session.merge(study)
            db_session.commit()
            study_tag_pairs = db_session.query(StudyTag).all()
            assert len(study_tag_pairs) == 2
            assert set(e.tag_label for e in study_tag_pairs) == {"test-tag-2", "test-tag-3"}
            assert set(e.study_id for e in study_tag_pairs) == {study_id_1}
