/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import type { Cluster } from "@/types/types";
import Matrix from "../../../../../../../common/Matrix";

interface Props {
  areaId: string;
  clusterId: Cluster["id"];
}

function RenewableMatrix({ areaId, clusterId }: Props) {
  return (
    <Matrix
      url={`input/renewables/series/${areaId}/${clusterId}/series`}
      title="study.modelization.clusters.matrix.timeSeries"
      aggregateColumns="stats"
    />
  );
}

export default RenewableMatrix;
