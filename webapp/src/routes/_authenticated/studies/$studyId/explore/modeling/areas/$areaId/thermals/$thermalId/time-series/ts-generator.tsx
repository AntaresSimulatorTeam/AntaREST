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
import useArea from "@/routes/-shared/hook/useArea";
import useStudy from "@/routes/-shared/hook/useStudy";
import { createFileRoute } from "@tanstack/react-router";
import { TS_GEN_MATRIX_COLS } from "../../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/$thermalId/time-series/ts-generator",
)({
  component: TimeSeriesGenerator,
});

function TimeSeriesGenerator() {
  const study = useStudy();
  const area = useArea();
  const { thermalId } = Route.useParams();

  return (
    <Matrix
      key={thermalId}
      studyId={study.id}
      url={`input/thermal/prepro/${area.id}/${thermalId}/data`}
      customColumns={TS_GEN_MATRIX_COLS}
      isTimeSeries={false}
      enableFilters
    />
  );
}
