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
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId/storages/$storageId",
)({
  component: StorageLayout,
});

function StorageLayout() {
  const params = Route.useParams();
  const { t } = useTranslation();

  return (
    <TabsView
      onBack={linkOptions({
        to: "/studies/$studyId/explore/modelization/areas/$areaId/storages",
        params,
      })}
      divider
      tabs={[
        {
          id: "parameters",
          label: t("study.modelization.storages.parameters"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modelization/areas/$areaId/storages/$storageId/parameters",
            params,
          }),
          // content: (
          //   <StorageForm
          //     studyId={studyId}
          //     studyVersion={study.version}
          //     areaId={areaId}
          //     storageId={storageId}
          //   />
          // ),
        },
        // {
        //   id: "time-series",
        //   label: t("global.timeSeries"),
        //   content: (
        //     <StorageMatrices studyVersion={study.version} areaId={areaId} storageId={storageId} />
        //   ),
        // },
        // semver.gte(study.version, "9.2.0") && {
        //   id: "additional-constraints",
        //   label: t("study.modelization.storages.additionalConstraints"),
        //   content: (
        //     <AdditionalConstraints
        //       studyId={studyId}
        //       areaId={areaId}
        //       storageId={nameToId(storageId)}
        //       studyVersion={study.version}
        //     />
        //   ),
        // },
      ].filter(Boolean)}
    />
  );
}
