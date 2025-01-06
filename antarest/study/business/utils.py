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

from antares.study.version import StudyVersion

from antarest.core.exceptions import CommandApplicationError
from antarest.core.interfaces.cache import CacheConstants
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.core.serialization import AntaresBaseModel
from antarest.study.business.all_optional_meta import camel_case_model
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.utils import is_managed
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener

# noinspection SpellCheckingInspection
GENERAL_DATA_PATH = "settings/generaldata"


def execute_or_add_commands(
    study: Study,
    file_study: FileStudy,
    commands: t.Sequence[ICommand],
    storage_service: StudyStorageService,
    listener: t.Optional[ICommandListener] = None,
) -> None:
    if isinstance(study, RawStudy):
        executed_commands: t.MutableSequence[ICommand] = []
        should_invalidate_cache = False
        for command in commands:
            if not command.can_update_study_config():
                should_invalidate_cache = True
            result = command.apply(file_study, listener)
            if not result.status:
                raise CommandApplicationError(result.message)
            executed_commands.append(command)
        # if commands that can't update the cache are applied, we need to invalidate it.
        # Otherwise, we can update it.
        if should_invalidate_cache:
            storage_service.variant_study_service.invalidate_cache(study)
        else:
            storage_service.raw_study_service.cache.put(
                f"{CacheConstants.STUDY_FACTORY}/{file_study.config.study_id}",
                FileStudyTreeConfigDTO.from_build_config(file_study.config).model_dump(mode="json"),
            )
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
    AntaresBaseModel,
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
    start_version: t.Optional[StudyVersion]
    end_version: t.Optional[StudyVersion]
    # Workaround to replace Pydantic computed values which are ignored by FastAPI.
    # TODO: check @computed_field available in Pydantic v2 to remove it
    # (value) -> encoded_value
    encode: t.Optional[t.Callable[[t.Any], t.Any]]
    # (encoded_value, current_value) -> decoded_value
    decode: t.Optional[t.Callable[[t.Any, t.Optional[t.Any]], t.Any]]
