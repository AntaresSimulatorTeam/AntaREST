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

from sqlalchemy.orm import Session

from antarest.study.business.model.link_model import Link
from antarest.study.dao.db.models import Link as LinkModel
from antarest.study.dao.db_link_dao import DbLinkDao
from tests.helpers import create_raw_study


class TestDbLinkDao:
    def test_save_and_get_links(self, db_session: Session):
        # Create a study
        study = create_raw_study(id="my-study", name="My Study")
        db_session.add(study)
        db_session.flush()

        # Create a DAO for this study
        dao = DbLinkDao(session=db_session, study_id=study.id)

        # Create a link
        link_data = Link(area1="a", area2="b")

        # Save the link
        dao.save_link(link_data)

        # Check if the link is saved in the database
        saved_link_model = db_session.query(LinkModel).one()
        assert saved_link_model.study_id == study.id
        assert saved_link_model.area1 == "a"
        assert saved_link_model.area2 == "b"

        # Check get_links
        links_from_dao = dao.get_links()
        assert len(links_from_dao) == 1
        assert links_from_dao[0].area1 == "a"
        assert links_from_dao[0].area2 == "b"

        # Check get_link
        single_link_from_dao = dao.get_link("a", "b")
        assert single_link_from_dao.area1 == "a"

    def test_delete_link(self, db_session: Session):
        # Create a study and a link
        study = create_raw_study(id="my-study", name="My Study")
        db_session.add(study)
        db_session.flush()

        link_model = LinkModel(study_id=study.id, area1="a", area2="b")
        db_session.add(link_model)
        db_session.commit()

        # Create a DAO and delete the link
        dao = DbLinkDao(session=db_session, study_id=study.id)
        link_to_delete = Link(area1="a", area2="b")
        dao.delete_link(link_to_delete)

        # Check that the link is deleted
        assert db_session.query(LinkModel).count() == 0
