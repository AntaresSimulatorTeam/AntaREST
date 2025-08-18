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

from typing import Sequence

from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.study.business.model.link_model import Link
from antarest.study.dao.db_link_dao import DbLinkDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class HybridDao(FileStudyTreeDao):
    def __init__(self, study: FileStudy, session: Session, study_id: str):
        super().__init__(study)
        self._db_link_dao = DbLinkDao(session, study_id)

    # --- LinkDao implementation ---

    @override
    def get_links(self) -> Sequence[Link]:
        # 1. Try to get links from the database
        links_from_db = self._db_link_dao.get_links()

        # 2. If links are found, return them
        if links_from_db:
            return links_from_db

        # 3. Else (Case B), assume it's an old study
        else:
            # a. Read links from filesystem
            links_from_fs = super().get_links()

            if links_from_fs:
                # b. Save them to the DB for next time (on-the-fly migration)
                for link in links_from_fs:
                    self._db_link_dao.save_link(link)

            # c. Return the links found in the filesystem
            return links_from_fs

    @override
    def get_link(self, area1_id: str, area2_id: str) -> Link:
        return self._db_link_dao.get_link(area1_id, area2_id)

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        return self._db_link_dao.link_exists(area1_id, area2_id)

    @override
    def save_link(self, link: Link) -> None:
        # First we save the metadata to the database
        self._db_link_dao.save_link(link)
        # Then wecall the original filesystem method to update the config files
        super().save_link(link)

    @override
    def delete_link(self, link: Link) -> None:
        # First we delete the metadata from the database
        self._db_link_dao.delete_link(link)
        # Then we call the original filesystem method to update the config files
        super().delete_link(link)

    # For series methods, we don't need to do anything special.
    # The call will be passed to the parent `FileStudyTreeDao`
    # which is the behavior we want.
