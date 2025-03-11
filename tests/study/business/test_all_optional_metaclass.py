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

from pydantic import Field

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model


class Model(AntaresBaseModel):
    float_with_default: float = 1
    float_without_default: float
    boolean_with_default: bool = True
    boolean_without_default: bool
    field_with_alias: str = Field(default="default", alias="field-with-alias")


@all_optional_model
class OptionalModel(Model):
    pass


@all_optional_model
@camel_case_model
class OptionalCamelCaseModel(Model):
    pass


def test_model() -> None:
    optional_model = OptionalModel()
    assert optional_model.float_with_default is None
    assert optional_model.float_without_default is None
    assert optional_model.boolean_with_default is None
    assert optional_model.boolean_without_default is None
    assert optional_model.field_with_alias is None

    optional_model = OptionalModel(boolean_with_default=False)
    assert optional_model.float_with_default is None
    assert optional_model.float_without_default is None
    assert optional_model.boolean_with_default is False
    assert optional_model.boolean_without_default is None
    assert optional_model.field_with_alias is None

    # build with alias should succeed
    args = {"field-with-alias": "test"}
    optional_model = OptionalModel(**args)
    assert optional_model.field_with_alias == "test"

    # build with camel_case should succeed
    args = {"fieldWithAlias": "test"}
    camel_case_model = OptionalCamelCaseModel(**args)
    assert camel_case_model.field_with_alias == "test"
