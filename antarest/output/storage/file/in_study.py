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
from typing_extensions import override

from antarest.core.interfaces.cache import ICache
from antarest.core.remote.remote_executor import IRemoteExecutor
from antarest.output.storage.file.abstract_storage import AbstractFileOutputStorage, IFileOutputsProvider
from antarest.output.storage.file.repository import FileOutputRepository
from antarest.output.storage.output_storage import OutputStorageType


class InStudyFileOutputStorage(AbstractFileOutputStorage):
    """
    Implementation based on outputs stored in antares-solver file format, inside a study.
    """

    def __init__(
        self,
        outputs_provider: IFileOutputsProvider,
        cache: ICache,
        remote_executor: IRemoteExecutor,
        repository: FileOutputRepository,
    ) -> None:
        super().__init__(outputs_provider, cache, remote_executor, repository, OutputStorageType.IN_STUDY_FILE_TREE)

    @override
    @property
    def storage_type(self) -> OutputStorageType:
        return OutputStorageType.IN_STUDY_FILE_TREE
