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
import pytest
from pydantic import TypeAdapter, ValidationError

from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import ItemName


def test_item_name_object_is_invalid():
    with pytest.raises(ValidationError):
        TypeAdapter(ItemName).validate_python([])


def test_item_name_only_special_characters_is_invalid():
    with pytest.raises(ValidationError):
        TypeAdapter(ItemName).validate_python("* .$")


def test_item_name_numeric_is_valid():
    assert TypeAdapter(ItemName).validate_python(872) == "872"


def test_item_str_is_valid():
    assert TypeAdapter(ItemName).validate_python("Gérard") == "Gérard"
