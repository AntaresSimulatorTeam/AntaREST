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
from antarest.study.business.model.binding_constraint_model import ClusterTerm, LinkTerm
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig


def remove_area_cluster_from_binding_constraints(
    study_data_config: FileStudyTreeConfig,
    area_id: str,
) -> None:
    for bc in study_data_config.bindings:
        for term in bc.terms:
            if (isinstance(term, ClusterTerm) and term.area == area_id) or (
                isinstance(term, LinkTerm) and (term.area1 == area_id or term.area2 == area_id)
            ):
                study_data_config.bindings.remove(bc)
                break
