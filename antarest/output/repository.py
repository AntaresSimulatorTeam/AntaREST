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

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.output.model import Output


class OutputRepository:
    def __init__(self, session: Session | None = None):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db.session
        return self._session

    def save(self, output_metadata: Output) -> Output:
        session = self.session
        output = session.merge(output_metadata)
        session.commit()
        return output

    def get(self, study_id: str, output_id: str) -> Output | None:
        stmt = select(Output).where((Output.output_id == output_id) & (Output.study_id == study_id))
        result = self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    def delete(self, study_id: str, output_id: str) -> None:

        session = self.session
        stmt = delete(Output).where(Output.output_id == output_id).where(Output.study_id == study_id)

        session.execute(stmt)
        session.commit()
