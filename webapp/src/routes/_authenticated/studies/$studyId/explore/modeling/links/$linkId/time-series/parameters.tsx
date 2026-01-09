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
import { parseLinkId } from "@/services/api/studies/links/utils";
import { checkRouteAvailability } from "@/utils/routerUtils";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { TABS_VIEW_MIN_VERSION } from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/links/$linkId/time-series/parameters",
)({
  component: Parameters,
});

function Parameters() {
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
    <Matrix
      key={linkId}
      studyId={study.id}
      url={`input/links/${area1}/${area2}_parameters`}
      title={t("study.modeling.links.matrix.parameters")}
      customColumns={[
        `${t("study.modeling.links.matrix.columns.hurdleCostsDirect")} (${area1}->${area2})`,
        `${t("study.modeling.links.matrix.columns.hurdleCostsIndirect")} (${area2}->${area1})`,
        t("study.modeling.links.matrix.columns.impedances"),
        t("study.modeling.links.matrix.columns.loopFlow"),
        t("study.modeling.links.matrix.columns.pShiftMin"),
        t("study.modeling.links.matrix.columns.pShiftMax"),
      ]}
      isTimeSeries={false}
      enableFilters
    />
  );
}
