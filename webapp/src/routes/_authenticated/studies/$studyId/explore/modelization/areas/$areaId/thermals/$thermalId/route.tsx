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

import TabsView from "@/components/page/TabsView";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId",
)({
  component: ThermalLayout,
});

function ThermalLayout() {
  const params = Route.useParams();
  const navigate = Route.useNavigate();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    // <>
    //   <BackButton onClick={() => navigate({ to: ".." })} />
    //   <ThermalForm study={study} areaId={area.id} clusterId={thermalId} />
    //   <Divider sx={{ my: 2 }} variant="middle">
    //     <Chip label={t("global.matrices")} size="small" />
    //   </Divider>
    //   <ThermalMatrices study={study} areaId={area.id} clusterId={nameToId(thermalId)} />
    // </>
    <TabsView
      onBack={linkOptions({
        to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals",
        params,
      })}
      tabs={[
        {
          id: "parameters",
          label: t("study.modelization.thermals.parameters"),
          linkOptions: {
            to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/parameters",
            params,
          },
        },
        {
          id: "matrices",
          label: t("study.modelization.thermals.matrices"),
          linkOptions: {
            to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/matrices",
            params,
          },
        },
      ]}
    />
  );
}
