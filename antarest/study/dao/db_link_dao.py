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

from antarest.core.exceptions import LinkNotFound
from antarest.study.business.model.link_model import Link as BusinessLink
from antarest.study.dao.api.link_dao import LinkDao
from antarest.study.dao.db.models import Link as DbLinkModel


def _db_to_business(link: DbLinkModel) -> BusinessLink:
    """Converts a database link model to a business link model."""
    return BusinessLink.model_validate(link, from_attributes=True)


def _business_to_db(link: BusinessLink, study_id: str) -> DbLinkModel:
    """Converts a business link model to a database link model."""
    db_link = DbLinkModel(
        **link.model_dump(),
        study_id=study_id,
    )
    return db_link


class DbLinkDao(LinkDao):
    def __init__(self, session: Session, study_id: str):
        self.session = session
        self.study_id = study_id

    @override
    def get_links(self) -> Sequence[BusinessLink]:
        db_links = self.session.query(DbLinkModel).filter_by(study_id=self.study_id).all()
        return [_db_to_business(link) for link in db_links]

    @override
    def get_link(self, area1_id: str, area2_id: str) -> BusinessLink:
        area1, area2 = sorted((area1_id, area2_id))
        db_link = (
            self.session.query(DbLinkModel).filter_by(study_id=self.study_id, area1=area1, area2=area2).one_or_none()
        )
        if db_link is None:
            raise LinkNotFound(f"Link between {area1} and {area2} not found in study {self.study_id}")
        return _db_to_business(db_link)

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        area1, area2 = sorted((area1_id, area2_id))
        return (
            self.session.query(DbLinkModel.study_id).filter_by(study_id=self.study_id, area1=area1, area2=area2).first()
            is not None
        )

    @override
    def save_link(self, link: BusinessLink) -> None:
        db_link = _business_to_db(link, self.study_id)
        self.session.merge(db_link)
        self.session.commit()

    @override
    def delete_link(self, link: BusinessLink) -> None:
        area1, area2 = sorted((link.area1, link.area2))
        db_link = self.session.query(DbLinkModel).filter_by(study_id=self.study_id, area1=area1, area2=area2).one()
        self.session.delete(db_link)
        self.session.commit()

    # These methods are filesystem-specific and will be handled by FileStudyLinkDao
    @override
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError("DB DAO does not handle time series data")

    @override
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError("DB DAO does not handle time series data")

    @override
    def save_link_series(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError("DB DAO does not handle time series data")
