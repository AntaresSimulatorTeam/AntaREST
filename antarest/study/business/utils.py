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

from typing import Any, Callable, Dict, MutableSequence, Optional, Sequence, TypedDict

from antares.study.version import StudyVersion

from antarest.core.exceptions import CommandApplicationError
from antarest.core.requests import RequestParameters
from antarest.core.serde import AntaresBaseModel
from antarest.login.utils import get_current_user
from antarest.study.business.all_optional_meta import camel_case_model
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.utils import is_managed
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import BindingConstraintProperties
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener

# noinspection SpellCheckingInspection
GENERAL_DATA_PATH = "settings/generaldata"


def execute_or_add_commands(
    study: Study,
    file_study: FileStudy,
    commands: Sequence[ICommand],
    storage_service: StudyStorageService,
    listener: Optional[ICommandListener] = None,
) -> None:
    # get current user if not in session, otherwise get session user
    current_user = get_current_user()

    if isinstance(study, RawStudy):
        executed_commands: MutableSequence[ICommand] = []
        for command in commands:
            result = command.apply(file_study, listener)
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
            RequestParameters(user=current_user),
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


def update_binding_constraint_from_props(bc: Dict[str, Any], bc_props: BindingConstraintProperties) -> None:
    bc_props_as_dict = bc_props.model_dump(mode="json", by_alias=True, exclude_unset=True)
    bc.update(bc_props_as_dict)
