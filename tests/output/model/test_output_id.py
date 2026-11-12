# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from antarest.output.model.output_id import OutputId, is_valid_output_id

_adapter = TypeAdapter(OutputId)


@pytest.mark.parametrize("output_id", ["20201014-1427eco", "20221003-2142adq", "out-sensitivity", "...", "a.b"])
def test_is_valid_output_id_accepts_valid_names(output_id: str) -> None:
    assert is_valid_output_id(output_id)


# Reject ids that escape or point at the outputs folder, incl. the Windows drive qualifier ("C:").
@pytest.mark.parametrize(
    "output_id",
    ["", ".", "..", "../x", "a/b", "/etc", "..\\", "a\\b", "a\nb", "a\rb", "C:", "C:..", "D:other", "c:foo"],
)
def test_is_valid_output_id_rejects_ids_that_escape_or_are_unsafe(output_id: str) -> None:
    assert not is_valid_output_id(output_id)


@pytest.mark.parametrize("output_id", ["20201014-1427eco", "out-sensitivity", "..."])
def test_output_id_type_accepts_valid_names(output_id: str) -> None:
    assert _adapter.validate_python(output_id) == output_id


# The `OutputId` type rejects an invalid id at the API edge, raising a validation error (HTTP 422).
@pytest.mark.parametrize("output_id", ["", ".", "..", "../x", "a/b", "a\nb", "C:", "D:other"])
def test_output_id_type_rejects_ids_that_escape_or_are_unsafe(output_id: str) -> None:
    with pytest.raises(ValidationError):
        _adapter.validate_python(output_id)
