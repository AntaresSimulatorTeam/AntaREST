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
import SplitView from "@/components/page/SplitView";
import useArea from "@/routes/-shared/hook/useArea";
import useStudy from "@/routes/-shared/hook/useStudy";
import { Box } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId/storages/$storageId/time-series/modulation",
)({
  component: Modulation,
});

function Modulation() {
  const study = useStudy();
  const area = useArea();
  const { storageId } = Route.useParams();
  const { t } = useTranslation();

  return (
    <SplitView splitId="storage-injectionModulation-withdrawalModulation" sizes={[50, 50]}>
      <Box sx={{ p: 2 }}>
        {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
        <Matrix
          studyId={study.id}
          title={t("study.modelization.storages.injectionModulation")}
          url={`input/st-storage/series/${area.id}/${storageId}/pmax_injection`}
          isTimeSeries={false}
          enableFilters
          customColumns={["TS 1"]}
        />
      </Box>
      <Box sx={{ p: 2 }}>
        {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
        <Matrix
          studyId={study.id}
          title={t("study.modelization.storages.withdrawalModulation")}
          url={`input/st-storage/series/${area.id}/${storageId}/pmax_withdrawal`}
          isTimeSeries={false}
          enableFilters
          customColumns={["TS 1"]}
        />
      </Box>
    </SplitView>
  );
}
