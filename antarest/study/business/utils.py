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

from typing import Any, Callable, Optional, TypedDict

from antares.study.version import StudyVersion

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.all_optional_meta import camel_case_model

# noinspection SpellCheckingInspection
GENERAL_DATA_PATH = "settings/generaldata"


@camel_case_model
class FormFieldsBaseModel(
    AntaresBaseModel,
    extra="forbid",
    validate_assignment=True,
    populate_by_name=True,
):
    """
    Pydantic Model for webapp form
    """


class FieldInfo(TypedDict, total=False):
    path: str
    default_value: Any
    start_version: Optional[StudyVersion]
    end_version: Optional[StudyVersion]
    # Workaround to replace Pydantic computed values which are ignored by FastAPI.
    # TODO: check @computed_field available in Pydantic v2 to remove it
    # (value) -> encoded_value
    encode: Optional[Callable[[Any], Any]]
    # (encoded_value, current_value) -> decoded_value
    decode: Optional[Callable[[Any, Optional[Any]], Any]]
