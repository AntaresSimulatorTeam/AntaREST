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

import Matrix from "@/components/Matrix";
import useStudy from "@/routes/-shared/hook/useStudy";
import { createFileRoute } from "@tanstack/react-router";
import semver from "semver";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series/inflows",
)({
  component: Inflows,
});

function Inflows() {
  const study = useStudy();
  const { areaId, storageId } = Route.useParams();

  return (
    <Matrix
      key={storageId}
      studyId={study.id}
      url={`input/st-storage/series/${areaId}/${storageId}/inflows`}
      // Since v9.3 this matrix supports the resize functionality
      {...(semver.lt(study.version, "9.3.0") && {
        isTimeSeries: false,
        customColumns: ["TS 1"],
        enableFilters: true,
      })}
    />
  );
}
