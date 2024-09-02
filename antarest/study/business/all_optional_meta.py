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
import copy

from pydantic import BaseModel, create_model

from antarest.core.utils.string import to_camel_case


def all_optional_model(model: t.Type[BaseModel]) -> t.Type[BaseModel]:
    kwargs = {}
    for field_name, field_info in model.model_fields.items():
        new = copy.deepcopy(field_info)
        new.default = None
        new.annotation = t.Optional[field_info.annotation]  # type: ignore
        kwargs[field_name] = (new.annotation, new)

    return create_model(f"Partial{model.__name__}", __base__=model, __module__=model.__module__, **kwargs)  # type: ignore


def camel_case_model(model: t.Type[BaseModel]) -> t.Type[BaseModel]:
    """
    This decorator can be used to modify a model to use camel case aliases.

    Args:
        model: The pydantic model to modify.

    Returns:
        The modified model.
    """
    model.model_config["alias_generator"] = to_camel_case
    for field_name, field in model.model_fields.items():
        new_alias = to_camel_case(field_name)
        field.alias = new_alias
        field.validation_alias = new_alias
        field.serialization_alias = new_alias
    return model
