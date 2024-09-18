/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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
  study: StudyMetadata;
  areaId: string;
  clusterId: Cluster["id"];
}

function Matrix({ study, areaId, clusterId }: Props) {
  const [t] = useTranslation();
  const [value, setValue] = React.useState(0);

  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
    >
      <Tabs value={value} onChange={(_, v) => setValue(v)} sx={{ width: 1 }}>
        <Tab label={t("study.modelization.clusters.matrix.timeSeries")} />
      </Tabs>
      <Box
        sx={{
          display: "flex",
          width: "100%",
          height: "100%",
        }}
      >
        <MatrixInput
          study={study}
          url={`input/renewables/series/${areaId}/${clusterId}/series`}
          computStats={MatrixStats.NOCOL}
          title={t("study.modelization.clusters.matrix.timeSeries")}
        />
      </Box>
    </Box>
  );
}

export default Matrix;
