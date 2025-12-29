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
import useStudy from "@/routes/-shared/hook/useStudy";
import { checkRouteAvailability } from "@/utils/routerUtils";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series/level-cost",
)({
  component: LevelCost,
});

function LevelCost() {
  const study = useStudy();
  const { areaId, storageId } = Route.useParams();
  const { t } = useTranslation();

  checkRouteAvailability({
    studyVersion: study.version,
    minVersion: "9.2.0",
    routePath: Route.path,
  });

  return (
    <Matrix
      key={storageId}
      studyId={study.id}
      title={t("study.modeling.storages.levelCost")}
      url={`input/st-storage/series/${areaId}/${storageId}/cost_level`}
      isTimeSeries={false}
      enableFilters
      customColumns={["TS 1"]}
    />
  );
}
