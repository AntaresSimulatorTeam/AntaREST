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
import useStudy from "@/routes/-shared/hook/useStudy";
import { parseLinkId } from "@/services/api/studies/links/utils";
import { checkRouteAvailability } from "@/utils/routerUtils";
import { Box } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { TABS_VIEW_MIN_VERSION } from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/links/$linkId/time-series/capacities",
)({
  component: Capacities,
});

function Capacities() {
  const { linkId } = Route.useParams();
  const study = useStudy();
  const { t } = useTranslation();
  const [area1, area2] = parseLinkId(linkId);

  checkRouteAvailability({
    studyVersion: study.version,
    minVersion: TABS_VIEW_MIN_VERSION,
    routePath: Route.path,
  });

  return (
    <SplitView splitId="link-transCapaDirect-transCapaIndirect" sizes={[50, 50]}>
      <Box sx={{ p: 2 }}>
        <Matrix
          key={linkId}
          studyId={study.id}
          url={`input/links/${area1}/capacities/${area2}_direct`}
          title={t("study.modeling.links.matrix.columns.transCapaDirect", {
            area1,
            area2,
          })}
        />
      </Box>
      <Box sx={{ p: 2 }}>
        <Matrix
          key={linkId}
          studyId={study.id}
          url={`input/links/${area1}/capacities/${area2}_indirect`}
          title={t("study.modeling.links.matrix.columns.transCapaIndirect", {
            area1,
            area2,
          })}
        />
      </Box>
    </SplitView>
  );
}
