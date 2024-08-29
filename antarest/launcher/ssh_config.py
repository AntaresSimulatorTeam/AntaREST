import pathlib
from typing import Any, Dict, Optional

import paramiko
from pydantic import BaseModel, model_validator


class SSHConfigDTO(BaseModel):
    config_path: pathlib.Path
    username: str
    hostname: str
    port: int = 22
    private_key_file: Optional[pathlib.Path] = None
    key_password: Optional[str] = ""
    password: Optional[str] = ""

    @model_validator(mode="before")
    def validate_connection_information(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "private_key_file" not in values and "password" not in values:
            raise paramiko.AuthenticationException("SSH config needs at least a private key or a password")
        return values
