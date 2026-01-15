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
import SplitView from "@/components/page/SplitView";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { checkRouteAvailability } from "@/utils/routerUtils";
import { Box } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series/variation-costs",
)({
  component: VariationCosts,
});

function VariationCosts() {
  const study = useStudy();
  const { areaId, storageId } = Route.useParams();
  const { t } = useTranslation();

  checkRouteAvailability({
    studyVersion: study.version,
    minVersion: "9.2.0",
    routePath: Route.path,
  });

  return (
    <SplitView splitId="storage-variationInjectionCost-variationWithdrawalCost" sizes={[50, 50]}>
      <Box sx={{ p: 2 }}>
        {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
        <Matrix
          key={storageId}
          studyId={study.id}
          title={t("study.modeling.storages.injectionVariationCost")}
          url={`input/st-storage/series/${areaId}/${storageId}/cost_variation_injection`}
          isTimeSeries={false}
          enableFilters
          customColumns={["TS 1"]}
        />
      </Box>
      <Box sx={{ p: 2 }}>
        {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
        <Matrix
          key={storageId}
          studyId={study.id}
          title={t("study.modeling.storages.withdrawalVariationCost")}
          url={`input/st-storage/series/${areaId}/${storageId}/cost_variation_withdrawal`}
          isTimeSeries={false}
          enableFilters
          customColumns={["TS 1"]}
        />
      </Box>
    </SplitView>
  );
}
