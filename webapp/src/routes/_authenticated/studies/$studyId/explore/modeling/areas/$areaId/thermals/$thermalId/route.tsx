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

import SelectFE, { type SelectFEChangeEvent } from "@/components/fieldEditors/SelectFE";
import TabsView from "@/components/page/TabsView";
import usePromise from "@/hooks/usePromise";
import { createFileRoute, linkOptions, useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { getThermalClusters } from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/$thermalId",
)({
  component: ThermalLayout,
});

function ThermalLayout() {
  const params = Route.useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { studyId, areaId, thermalId } = params;

  const { data: thermalOptions = [thermalId], status: thermalOptionsStatus } =
    usePromise(async () => {
      const thermals = await getThermalClusters(studyId, areaId);

      return thermals.map((thermal) => ({
        label: thermal.name,
        value: thermal.id,
        group: thermal.group,
      }));
    }, [studyId, areaId]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: SelectFEChangeEvent<string>) => {
    const newThermalId = event.target.value;

    navigate({
      to: ".",
      params: {
        ...params,
        thermalId: newThermalId,
      },
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      onBack={linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/thermals",
        params,
      })}
      divider
      tabs={[
        {
          id: "parameters",
          label: t("study.modeling.thermals.parameters"),
          linkOptions: {
            to: "/studies/$studyId/explore/modeling/areas/$areaId/thermals/$thermalId/parameters",
            params,
          },
        },
        {
          id: "time-series",
          label: t("global.timeSeries"),
          linkOptions: {
            to: "/studies/$studyId/explore/modeling/areas/$areaId/thermals/$thermalId/time-series",
            params,
          },
        },
      ]}
      secondaryActions={
        <SelectFE
          label={t("study.modeling.thermals.select")}
          value={thermalId}
          options={thermalOptions}
          onChange={handleChange}
          size="extra-small"
          disabled={thermalOptionsStatus !== "fulfilled"}
          sx={{ minWidth: 90, maxWidth: 150 }}
        />
      }
    />
  );
}
