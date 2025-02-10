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

import pathlib
from typing import Any, Dict, Optional

import paramiko
from pydantic import model_validator

from antarest.core.serde import AntaresBaseModel


class SSHConfigDTO(AntaresBaseModel):
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
