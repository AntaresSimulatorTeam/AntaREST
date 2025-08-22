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
from abc import ABC, abstractmethod
from typing import Sequence

from antarest.study.business.model.layer_model import Layer, LayerUpdate


class ReadOnlyLayerDao(ABC):
    @abstractmethod
    def get_layers(self) -> Sequence[Layer]:
        raise NotImplementedError()


class LayerDao(ReadOnlyLayerDao):
    @abstractmethod
    def save_layers(self, layer: Layer) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_layer(self, layer: Layer) -> None:
        raise NotImplementedError()
