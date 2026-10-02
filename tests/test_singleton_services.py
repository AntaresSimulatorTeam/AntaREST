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
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from antarest.service_creator import Module
from antarest.singleton_services import _init

# The factory `_init` is expected to call for each module it can start.
# `Module.APP` is absent on purpose: the application server is started by `main.py`.
MODULE_FACTORIES = {
    Module.WATCHER: "create_watcher",
    Module.MATRIX_GC: "create_matrix_gc",
    Module.BLOB_GC: "create_blob_gc",
    Module.VARIABLE_VIEW_GC: "create_variable_view_gc",
    Module.AUTO_ARCHIVER: "AutoArchiveService",
    Module.ARCHIVE_WORKER: "create_archive_worker",
}


@pytest.fixture
def factories(mocker: MockerFixture) -> dict[Module, MagicMock]:
    """Neutralize everything `_init` does besides dispatching modules to factories."""
    for dependency in ("Config", "init_db_engine", "init_db_singleton", "configure_logger", "create_core_services"):
        mocker.patch(f"antarest.singleton_services.{dependency}")
    # `create=True` so that a factory missing from `_init` fails on the assertion below,
    # which names the culprit module, rather than on the patching itself.
    return {
        module: mocker.patch(f"antarest.singleton_services.{name}", create=True)
        for module, name in MODULE_FACTORIES.items()
    }


def test_all_modules_are_startable() -> None:
    """Guard against a module added to `Module`, hence to the `--module` choices, but not to `_init`."""
    assert set(MODULE_FACTORIES) == set(Module) - {Module.APP}


@pytest.mark.parametrize("module", list(MODULE_FACTORIES))
def test_module_starts_its_own_service(module: Module, factories: dict[Module, MagicMock]) -> None:
    assert _init(Path("application.yaml"), [module]) == [factories[module].return_value]
