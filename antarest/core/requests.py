import typing as t
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Generator, Tuple

from fastapi import HTTPException
from markupsafe import escape
from ratelimit import Rule  # type: ignore

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

    def __setitem__(self, key: str, value: t.Any) -> None:
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key: str) -> t.Any:
        return self._store[key.lower()][1]

    def __delitem__(self, key: str) -> None:
        del self._store[key.lower()]

    def __iter__(self) -> t.Any:
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def lower_items(self) -> Generator[Tuple[Any, Any], Any, None]:
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    def __eq__(self, other: t.Any) -> bool:
        if isinstance(other, t.Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        return dict(self.lower_items()) == dict(other.lower_items())

    def copy(self) -> "CaseInsensitiveDict":
        return CaseInsensitiveDict(self._store.values())

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
