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

from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.area_model import DEFAULT_LAYER_ID, DEFAULT_LAYER_NAME
from antarest.study.business.model.layer_model import Layer
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import Study


class DataBaseStudyDaoFactory(StudyFactoryDao):
    """
    Used to initialize a study inside DB
    """

    def __init__(self, matrix_service: ISimpleMatrixService, session: Session | None = None) -> None:
        self._matrix_service = matrix_service
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    @override
    def create_study_dao(self, study: Study) -> DatabaseStudyDao:
        dao = DatabaseStudyDao(study.id, self.session, self._matrix_service)
        dao.save_layer(Layer(id=DEFAULT_LAYER_ID, name=DEFAULT_LAYER_NAME))
        return dao
