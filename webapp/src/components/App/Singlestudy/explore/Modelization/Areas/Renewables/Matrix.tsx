/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import * as React from "react";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import { useTranslation } from "react-i18next";
import {
  Cluster,
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../common/types";
import MatrixInput from "../../../../../../common/MatrixInput";

interface Props {
  areaId: string;
  clusterId: Cluster["id"];
}

function RenewablesMatrix({ areaId, clusterId }: Props) {
  return (
    <Matrix
      url={`input/renewables/series/${areaId}/${clusterId}/series`}
      title="study.modelization.clusters.matrix.timeSeries"
    />
  );
}

export default RenewablesMatrix;
