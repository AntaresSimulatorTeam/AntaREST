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
import { COMMON_MATRIX_COLS } from "../../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/matrices/common",
)({
  component: Common,
});

function Common() {
  const study = useStudy();
  const area = useArea();
  const { thermalId } = Route.useParams();

  return (
    <Matrix
      studyId={study.id}
      url={`input/thermal/prepro/${area.id}/${thermalId}/modulation`}
      customColumns={COMMON_MATRIX_COLS}
      isTimeSeries={false}
      enableFilters
    />
  );
}
