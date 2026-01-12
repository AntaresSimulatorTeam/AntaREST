/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import TabsView from "@/components/common/TabsView";
import type { Cluster, StudyMetadata } from "@/types/types";
import { useTranslation } from "react-i18next";
import semver from "semver";
import Matrix from "../../../../../../../common/Matrix";
import { COMMON_MATRIX_COLS, TS_GEN_MATRIX_COLS } from "../utils";

interface Props {
  study: StudyMetadata;
  areaId: string;
  clusterId: Cluster["id"];
}

function ThermalMatrices({ study, areaId, clusterId }: Props) {
  const [t] = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      disableGutters
      items={[
        {
          label: t("study.modelization.clusters.matrix.common"),
          content: (
            <Matrix
              url={`input/thermal/prepro/${areaId}/${clusterId}/modulation`}
              customColumns={COMMON_MATRIX_COLS}
              isTimeSeries={false}
              enableFilters
            />
          ),
        },
        {
          label: t("study.modelization.clusters.matrix.tsGen"),
          content: (
            <Matrix
              url={`input/thermal/prepro/${areaId}/${clusterId}/data`}
              customColumns={TS_GEN_MATRIX_COLS}
              isTimeSeries={false}
              enableFilters
            />
          ),
        },
        {
          label: t("study.modelization.clusters.matrix.availability"),
          content: (
            <Matrix
              url={`input/thermal/series/${areaId}/${clusterId}/series`}
              aggregateColumns="stats" // avg, min, max
            />
          ),
        },
        semver.gte(study.version, "8.7.0") && {
          label: t("study.modelization.clusters.matrix.fuelCosts"),
          content: <Matrix url={`input/thermal/series/${areaId}/${clusterId}/fuelCost`} />,
        },
        semver.gte(study.version, "8.7.0") && {
          label: t("study.modelization.clusters.matrix.co2Costs"),
          content: <Matrix url={`input/thermal/series/${areaId}/${clusterId}/CO2Cost`} />,
        },
      ].filter(Boolean)}
    />
  );
}

export default ThermalMatrices;
