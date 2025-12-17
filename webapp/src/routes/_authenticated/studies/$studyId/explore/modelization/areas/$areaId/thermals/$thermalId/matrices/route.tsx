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

import Matrix from "@/components/Matrix";
import TabsView from "@/components/page/TabsView";
import useArea from "@/routes/-shared/hook/useArea";
import useStudy from "@/routes/-shared/hook/useStudy";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import { COMMON_MATRIX_COLS, TS_GEN_MATRIX_COLS } from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/matrices",
)({
  component: Matrices,
});

function Matrices() {
  const study = useStudy();
  const area = useArea();
  const { thermalId } = Route.useParams();
  const [t] = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      tabs={[
        {
          id: "common",
          label: t("study.modelization.clusters.matrix.common"),
          content: (
            <Matrix
              studyId={study.id}
              url={`input/thermal/prepro/${area.id}/${thermalId}/modulation`}
              customColumns={COMMON_MATRIX_COLS}
              isTimeSeries={false}
              enableFilters
            />
          ),
        },
        {
          id: "ts-gen",
          label: t("study.modelization.clusters.matrix.tsGen"),
          content: (
            <Matrix
              studyId={study.id}
              url={`input/thermal/prepro/${area.id}/${thermalId}/data`}
              customColumns={TS_GEN_MATRIX_COLS}
              isTimeSeries={false}
              enableFilters
            />
          ),
        },
        {
          id: "availability",
          label: t("study.modelization.clusters.matrix.availability"),
          content: (
            <Matrix
              studyId={study.id}
              url={`input/thermal/series/${area.id}/${thermalId}/series`}
              aggregateColumns="stats" // avg, min, max
            />
          ),
        },
        semver.gte(study.version, "8.7.0") && {
          id: "fuel-costs",
          label: t("study.modelization.clusters.matrix.fuelCosts"),
          content: (
            <Matrix
              studyId={study.id}
              url={`input/thermal/series/${area.id}/${thermalId}/fuelCost`}
            />
          ),
        },
        semver.gte(study.version, "8.7.0") && {
          id: "co2-costs",
          label: t("study.modelization.clusters.matrix.co2Costs"),
          content: (
            <Matrix
              studyId={study.id}
              url={`input/thermal/series/${area.id}/${thermalId}/CO2Cost`}
            />
          ),
        },
      ].filter(Boolean)}
    />
  );
}
