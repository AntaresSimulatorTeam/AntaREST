from dataclasses import dataclass
from typing import Optional

from dataclasses_json.api import dataclass_json

from antarest.common.config import register_config


@dataclass
class LoginInfo:
    pwd: str


@dataclass
class DefaultLogins:
    admin: LoginInfo


@dataclass
class JwtConfig:
    key: str


@dataclass_json
@dataclass
class SecurityConfig:
    disabled: bool = True
    login: Optional[DefaultLogins] = None
    jwt: Optional[JwtConfig] = None


get_config = register_config("security", SecurityConfig)
