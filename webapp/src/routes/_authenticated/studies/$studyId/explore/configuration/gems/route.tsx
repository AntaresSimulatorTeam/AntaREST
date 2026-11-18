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

import TabsView from "@/components/page/TabsView";
import { StorageMode } from "@/types/types";
import { checkRouteAvailability } from "@/utils/routerUtils";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import useStudy from "../../../-hooks/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/configuration/gems")(
  {
    component: GemsLayout,
  },
);

function GemsLayout() {
  const { t } = useTranslation();
  const params = Route.useParams();
  const study = useStudy();

  checkRouteAvailability({
    study,
    minVersion: "10.2.0",
    requiredStorageMode: StorageMode.DATABASE,
    routePath: Route.path,
  });

  return (
    <TabsView
      tabs={[
        {
          id: "scenarioBuilder",
          label: t("study.configuration.gems.tab.scenarioBuilder"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/gems/scenario-builder",
            params,
          }),
        },
      ]}
    />
  );
}
