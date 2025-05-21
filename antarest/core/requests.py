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

from collections import OrderedDict
from typing import Any, Generator, Mapping, MutableMapping, Tuple

from fastapi import HTTPException
from ratelimit import Rule  # type: ignore
from typing_extensions import override

RATE_LIMIT_CONFIG = {
    r"^/v1/launcher/run": [
        Rule(second=1, minute=20),
    ],
    r"^/v1/watcher/_scan": [
        Rule(minute=2),
    ],
}


class CaseInsensitiveDict(MutableMapping[str, Any]):  # copy of the requests class to avoid importing the package
    def __init__(self, data=None, **kwargs) -> None:  # type: ignore
        self._store: OrderedDict[str, Any] = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    @override
    def __setitem__(self, key: str, value: Any) -> None:
        self._store[key.lower()] = (key, value)

    @override
    def __getitem__(self, key: str) -> Any:
        return self._store[key.lower()][1]

    @override
    def __delitem__(self, key: str) -> None:
        del self._store[key.lower()]

    @override
    def __iter__(self) -> Any:
        return (casedkey for casedkey, mappedvalue in self._store.values())

    @override
    def __len__(self) -> int:
        return len(self._store)

    def lower_items(self) -> Generator[Tuple[Any, Any], Any, None]:
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    @override
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        return dict(self.lower_items()) == dict(other.lower_items())

    def copy(self) -> "CaseInsensitiveDict":
        return CaseInsensitiveDict(self._store.values())

    @override
    def __repr__(self) -> str:
        return str(dict(self.items()))


class UserHasNotPermissionError(HTTPException):
    def __init__(self, msg: str = "Permission denied") -> None:
        super().__init__(status_code=403, detail=msg)


class MustBeAuthenticatedError(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=403, detail="Permission denied")
