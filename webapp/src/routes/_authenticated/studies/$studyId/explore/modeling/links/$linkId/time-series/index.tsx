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
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { parseLinkId } from "@/services/api/studies/links/utils";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import semver from "semver";
import { TABS_VIEW_MIN_VERSION } from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/links/$linkId/time-series/",
)({
  component: TimeSeries,
});

function TimeSeries() {
  const { linkId } = Route.useParams();
  const navigate = Route.useNavigate();
  const study = useStudy();
  const { t } = useTranslation();
  const [area1, area2] = parseLinkId(linkId);
  const isTabsView = semver.gte(study.version, TABS_VIEW_MIN_VERSION);

  useEffect(() => {
    if (isTabsView) {
      navigate({
        from: Route.fullPath,
        to: "parameters",
        replace: true,
      });
    }
  }, [isTabsView, linkId, navigate, study.id, study.version]);

  if (!isTabsView) {
    return (
      <Matrix
        studyId={study.id}
        url={`input/links/${area1}/${area2}`}
        customColumns={[
          t("study.modeling.links.matrix.columns.transCapaDirect"),
          t("study.modeling.links.matrix.columns.transCapaIndirect"),
          `${t("study.modeling.links.matrix.columns.hurdleCostsDirect")} (${area1}->${area2})`,
          `${t("study.modeling.links.matrix.columns.hurdleCostsIndirect")} (${area2}->${area1})`,
          t("study.modeling.links.matrix.columns.impedances"),
          t("study.modeling.links.matrix.columns.loopFlow"),
          t("study.modeling.links.matrix.columns.pShiftMin"),
          t("study.modeling.links.matrix.columns.pShiftMax"),
        ]}
      />
    );
  }

  return null;
}
