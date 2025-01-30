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

import typing as t
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Generator, Tuple

from fastapi import HTTPException
from markupsafe import escape
from ratelimit import Rule  # type: ignore
from typing_extensions import override

from antarest.core.jwt import JWTUser

RATE_LIMIT_CONFIG = {
    r"^/v1/launcher/run": [
        Rule(second=1, minute=20),
    ],
    r"^/v1/watcher/_scan": [
        Rule(minute=2),
    ],
}


class CaseInsensitiveDict(t.MutableMapping[str, t.Any]):  # copy of the requests class to avoid importing the package
    def __init__(self, data=None, **kwargs) -> None:  # type: ignore
        self._store: OrderedDict[str, t.Any] = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    @override
    def __setitem__(self, key: str, value: t.Any) -> None:
        self._store[key.lower()] = (key, value)

    @override
    def __getitem__(self, key: str) -> t.Any:
        return self._store[key.lower()][1]

    @override
    def __delitem__(self, key: str) -> None:
        del self._store[key.lower()]

    @override
    def __iter__(self) -> t.Any:
        return (casedkey for casedkey, mappedvalue in self._store.values())

    @override
    def __len__(self) -> int:
        return len(self._store)

    def lower_items(self) -> Generator[Tuple[Any, Any], Any, None]:
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    @override
    def __eq__(self, other: t.Any) -> bool:
        if isinstance(other, t.Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        return dict(self.lower_items()) == dict(other.lower_items())

    def copy(self) -> "CaseInsensitiveDict":
        return CaseInsensitiveDict(self._store.values())

    @override
    def __repr__(self) -> str:
        return str(dict(self.items()))


@dataclass
class RequestParameters:
    """
    DTO object to handle data inside request to send to service
    """

    user: t.Optional[JWTUser] = None

    def get_user_id(self) -> str:
        return str(escape(str(self.user.id))) if self.user else "Unknown"


class UserHasNotPermissionError(HTTPException):
    def __init__(self, msg: str = "Permission denied") -> None:
        super().__init__(status_code=403, detail=msg)


class MustBeAuthenticatedError(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=403, detail="Permission denied")
