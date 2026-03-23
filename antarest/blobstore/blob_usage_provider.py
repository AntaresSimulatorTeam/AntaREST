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
from abc import ABC, abstractmethod
from collections.abc import Iterable

from antarest.blobstore.model import BlobReference


class IBlobUsageProvider(ABC):
    """
    Provide informations about which blobs are used by a client of the blob service
    """

    @abstractmethod
    def get_blob_usage(self) -> Iterable[BlobReference]:
        raise NotImplementedError()
