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

import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";

import { Cluster, StudyMetadata } from "@/common/types";
import Matrix from "@/components/common/Matrix";

import { COMMON_MATRIX_COLS, TS_GEN_MATRIX_COLS } from "./utils";

interface Props {
  study: StudyMetadata;
  areaId: string;
  clusterId: Cluster["id"];
}

function ThermalMatrices({ study, areaId, clusterId }: Props) {
  const [t] = useTranslation();
  const [value, setValue] = useState("common");
  const studyVersion = Number(study.version);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setValue(newValue);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const MATRICES = [
    {
      url: `input/thermal/prepro/${areaId}/${clusterId}/modulation`,
      titleKey: "common",
      columns: COMMON_MATRIX_COLS,
    },
    {
      url: `input/thermal/prepro/${areaId}/${clusterId}/data`,
      titleKey: "tsGen",
      columns: TS_GEN_MATRIX_COLS,
    },
    {
      url: `input/thermal/series/${areaId}/${clusterId}/series`,
      titleKey: "availability",
      aggregates: "stats" as const, // avg, min, max
    },
    {
      url: `input/thermal/series/${areaId}/${clusterId}/fuelCost`,
      titleKey: "fuelCosts",
      minVersion: 870,
    },
    {
      url: `input/thermal/series/${areaId}/${clusterId}/CO2Cost`,
      titleKey: "co2Costs",
      minVersion: 870,
    },
  ];

  // Filter matrix data based on the study version.
  const filteredMatrices = useMemo(
    () =>
      MATRICES.filter(({ minVersion }) =>
        minVersion ? studyVersion >= minVersion : true,
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [studyVersion],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        width: 1,
        height: 1,
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
      }}
    >
      <Tabs sx={{ width: 1 }} value={value} onChange={handleTabChange}>
        {filteredMatrices.map(({ titleKey }) => (
          <Tab
            key={titleKey}
            value={titleKey}
            label={t(`study.modelization.clusters.matrix.${titleKey}`)}
          />
        ))}
      </Tabs>
      <Box sx={{ width: 1, height: 1 }}>
        {filteredMatrices.map(
          ({ url, titleKey, columns, aggregates }) =>
            value === titleKey && (
              <Matrix
                key={titleKey}
                url={url}
                title={t(`study.modelization.clusters.matrix.${titleKey}`)}
                customColumns={columns}
                aggregateColumns={aggregates}
              />
            ),
        )}
      </Box>
    </Box>
  );
}

export default ThermalMatrices;
