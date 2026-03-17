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
import { getRenewableClusters } from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/renewables/$renewableId",
)({
  component: RenewablesLayout,
});

function RenewablesLayout() {
  const params = Route.useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { studyId, areaId, renewableId } = params;

  const { data: renewableOptions = [renewableId], status: renewableOptionsStatus } =
    usePromise(async () => {
      const renewables = await getRenewableClusters(studyId, areaId);

      return renewables.map((renewable) => ({
        label: renewable.name,
        value: renewable.id,
        group: renewable.group,
      }));
    }, [studyId, areaId]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: SelectFEChangeEvent<string>) => {
    const newRenewableId = event.target.value;

    navigate({
      to: ".",
      params: {
        ...params,
        renewableId: newRenewableId,
      },
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      onBack={linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/renewables",
        params,
      })}
      divider
      tabs={[
        {
          id: "parameters",
          label: t("study.modeling.renewables.parameters"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/renewables/$renewableId/parameters",
            params,
          }),
        },
        {
          id: "time-series",
          label: t("global.timeSeries"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/renewables/$renewableId/time-series",
            params,
          }),
        },
      ]}
      primaryActions={
        <SelectFE
          label={t("study.modeling.renewables.select")}
          value={params.renewableId}
          options={renewableOptions}
          onChange={handleChange}
          size="extra-small"
          disabled={renewableOptionsStatus !== "fulfilled"}
          sx={{ minWidth: 90, maxWidth: 150 }}
        />
      }
    />
  );
}
