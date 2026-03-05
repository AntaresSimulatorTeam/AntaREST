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

"""
Task action descriptor and registry for serializable task dispatch.

Instead of passing closures (which can't be serialized for Celery),
callers create a TaskActionDescriptor with a registered action_type
and JSON-serializable params. The registry maps action types to handler
functions that can be looked up both in-process and in Celery workers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, ClassVar

from antarest.core.serde import AntaresBaseModel
from antarest.core.tasks.model import TaskResult

if TYPE_CHECKING:
    from antarest.core.tasks.service import ITaskNotifier
    from antarest.service_creator import CoreServices


class TaskActionDescriptor(AntaresBaseModel, extra="forbid"):
    """Serializable task description sent to workers."""

    action_type: str
    """Registry key, e.g. ``"archive_study"``."""
    params: dict[str, Any] = {}
    """JSON-serializable parameters for the handler."""


class TaskActionParams(AntaresBaseModel):
    """Base class for typed task action parameters.

    Each action type should define a subclass with its specific fields.
    """


# Type alias for handler callables that accept validated params.
# We use Any for the params argument because each handler receives
# its own specific TaskActionParams subclass.
TaskActionHandler = Callable[["CoreServices", Any, "ITaskNotifier"], TaskResult]

_HandlerEntry = tuple[TaskActionHandler, type[TaskActionParams]]


class TaskActionRegistry:
    """Global registry mapping action type strings to handler callables."""

    _handlers: ClassVar[dict[str, _HandlerEntry]] = {}

    @classmethod
    def register(
        cls, action_type: str, params_model: type[TaskActionParams]
    ) -> Callable[[TaskActionHandler], TaskActionHandler]:
        """Decorator to register a handler for a given action type.

        Usage::

            class ArchiveStudyParams(TaskActionParams):
                study_id: str

            @TaskActionRegistry.register("archive_study", ArchiveStudyParams)
            def handle_archive_study(services, params: ArchiveStudyParams, notifier):
                ...
        """

        def decorator(fn: TaskActionHandler) -> TaskActionHandler:
            if action_type in cls._handlers:
                raise ValueError(f"Action type '{action_type}' is already registered")
            cls._handlers[action_type] = (fn, params_model)
            return fn

        return decorator

    @classmethod
    def get_handler(cls, action_type: str) -> _HandlerEntry:
        """Look up a handler and its params model by action type.

        Returns:
            A tuple of (handler_function, params_model_class).

        Raises:
            KeyError: if the action type is not registered.
        """
        try:
            return cls._handlers[action_type]
        except KeyError:
            raise KeyError(f"No handler registered for action type '{action_type}'") from None

    @classmethod
    def _clear(cls) -> None:
        """For testing only: clear all registered handlers."""
        cls._handlers.clear()
