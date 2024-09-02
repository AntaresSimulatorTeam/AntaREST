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

from antarest.core.exceptions import ReferencedObjectDeletionNotAllowed


class TestReferencedObjectDeletionNotAllowed:
    def test_few_binding_constraints(self) -> None:
        object_id = "france"
        binding_ids = ["bc1", "bc2"]
        object_type = "Area"
        exception = ReferencedObjectDeletionNotAllowed(object_id, binding_ids, object_type=object_type)
        message = str(exception)
        assert f"{object_type} '{object_id}'" in message
        assert "bc1" in message
        assert "bc2" in message
        assert "more..." not in message

    def test_many_binding_constraints(self) -> None:
        object_id = "france"
        binding_ids = [f"bc{i}" for i in range(1, 50)]
        object_type = "Area"
        exception = ReferencedObjectDeletionNotAllowed(object_id, binding_ids, object_type=object_type)
        message = str(exception)
        assert f"{object_type} '{object_id}'" in message
        assert "bc1" in message
        assert "bc2" in message
        assert "more..." in message
