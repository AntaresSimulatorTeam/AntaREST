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

import typing as t

from pydantic import BaseModel

from antarest.core.exceptions import CommandApplicationError
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.study.business.all_optional_meta import camel_case_model
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.utils import is_managed
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.model.command.icommand import ICommand

# noinspection SpellCheckingInspection
GENERAL_DATA_PATH = "settings/generaldata"


def execute_or_add_commands(
    study: Study,
    file_study: FileStudy,
    commands: t.Sequence[ICommand],
    storage_service: StudyStorageService,
) -> None:
    if isinstance(study, RawStudy):
        executed_commands: t.MutableSequence[ICommand] = []
        for command in commands:
            result = command.apply(file_study)
            if not result.status:
                raise CommandApplicationError(result.message)
            executed_commands.append(command)
        storage_service.variant_study_service.invalidate_cache(study)
        if not is_managed(study):
            # In a previous version, de-normalization was performed asynchronously.
            # However, this cause problems with concurrent file access,
            # especially when de-normalizing a matrix (which can take time).
            #
            # async_denormalize = threading.Thread(
            #     name=f"async_denormalize-{study.id}",
            #     target=file_study.tree.denormalize,
            # )
            # async_denormalize.start()
            #
            # To avoid this concurrency problem, it would be necessary to implement a
            # locking system for the entire study using a file lock (since multiple processes,
            # not only multiple threads, could access the same content simultaneously).
            #
            # Currently, we use a synchronous call to address the concurrency problem
            # within the current process (not across multiple processes)...
            file_study.tree.denormalize()
    else:
        storage_service.variant_study_service.append_commands(
            study.id,
            transform_command_to_dto(commands, force_aggregate=True),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )


@camel_case_model
class FormFieldsBaseModel(
    BaseModel,
    extra="forbid",
    validate_assignment=True,
    populate_by_name=True,
):
    """
    Pydantic Model for webapp form
    """


class FieldInfo(t.TypedDict, total=False):
    path: str
    default_value: t.Any
    start_version: t.Optional[int]
    end_version: t.Optional[int]
    # Workaround to replace Pydantic computed values which are ignored by FastAPI.
    # TODO: check @computed_field available in Pydantic v2 to remove it
    # (value) -> encoded_value
    encode: t.Optional[t.Callable[[t.Any], t.Any]]
    # (encoded_value, current_value) -> decoded_value
    decode: t.Optional[t.Callable[[t.Any, t.Optional[t.Any]], t.Any]]
