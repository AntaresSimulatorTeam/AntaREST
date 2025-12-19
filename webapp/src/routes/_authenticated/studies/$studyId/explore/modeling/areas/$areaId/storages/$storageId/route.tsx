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

import SelectFE, { type SelectFEChangeEvent } from "@/components/fieldEditors/SelectFE";
import TabsView from "@/components/page/TabsView";
import usePromise from "@/hooks/usePromise";
import useArea from "@/routes/-shared/hook/useArea";
import useStudy from "@/routes/-shared/hook/useStudy";
import { createFileRoute, linkOptions, useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { getStorages } from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId",
)({
  component: StorageLayout,
});

function StorageLayout() {
  const study = useStudy();
  const area = useArea();
  const params = Route.useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const { data: storageOptions = [params.storageId], status: storageOptionsStatus } =
    usePromise(async () => {
      const storages = await getStorages(study.id, area.id);

      return storages.map((storage) => ({
        label: storage.name,
        value: storage.id,
        group: storage.group,
      }));
    }, [study.id, area.id]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: SelectFEChangeEvent<string>) => {
    const newStorageId = event.target.value;

    navigate({
      to: ".",
      params: {
        ...params,
        storageId: newStorageId,
      },
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      onBack={linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages",
        params,
      })}
      divider
      tabs={[
        {
          id: "parameters",
          label: t("study.modeling.storages.parameters"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/parameters",
            params,
          }),
        },
        {
          id: "time-series",
          label: t("global.timeSeries"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series",
            params,
          }),
        },
        // semver.gte(study.version, "9.2.0") && {
        //   id: "additional-constraints",
        //   label: t("study.modeling.storages.additionalConstraints"),
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
      extraActions={
        <SelectFE
          value={params.storageId}
          options={storageOptions}
          onChange={handleChange}
          size="extra-small"
          disabled={storageOptionsStatus !== "fulfilled"}
          sx={{ maxWidth: 150 }}
        />
      }
    />
  );
}
