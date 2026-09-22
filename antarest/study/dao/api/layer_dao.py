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
from collections.abc import Sequence

from antarest.study.business.model.layer_model import Layer


class ReadOnlyLayerDao(ABC):
    @abstractmethod
    def get_layers(self) -> Sequence[Layer]:
        raise NotImplementedError()

    @abstractmethod
    def layer_exists(self, layer_id: str) -> bool:
        raise NotImplementedError()


class LayerDao(ReadOnlyLayerDao):
    @abstractmethod
    def save_layer(self, layer: Layer) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_layer(self, layer_id: str) -> None:
        raise NotImplementedError()
