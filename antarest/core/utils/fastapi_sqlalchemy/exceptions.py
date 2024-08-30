# Copyright (c) 2024, RTE (https://www.rte-france.com)
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


class MissingSessionError(Exception):
    """Exception raised for when the user tries to access a database session before it is created."""

    def __init__(self) -> None:
        msg = """
        No session found! Either you are not currently in a request context,
        or you need to manually create a session context by using a `db` instance as
        a context manager e.g.:

        with db():
            db.session.query(User).all()
        """

        super().__init__(msg)


class SessionNotInitialisedError(Exception):
    """Exception raised when the user creates a new DB session without first initialising it."""

    def __init__(self) -> None:
        msg = """
        Session not initialised! Ensure that DBSessionMiddleware has been initialised before
        attempting database access.
        """

        super().__init__(msg)
