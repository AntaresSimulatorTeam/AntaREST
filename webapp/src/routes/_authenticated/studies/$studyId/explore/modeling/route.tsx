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
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/modeling")({
  component: ModelingLayout,
});

function ModelingLayout() {
  const { t } = useTranslation();
  const params = Route.useParams();

  return (
    <TabsView
      tabs={[
        {
          id: "map",
          label: t("study.modeling.map"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/map",
            params,
          }),
        },
        {
          id: "areas",
          label: t("study.areas"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas",
            params,
          }),
        },
        {
          id: "links",
          label: t("study.links"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/links",
            params,
          }),
        },
        {
          id: "binding-constraints",
          label: t("study.bindingConstraints"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/binding-constraints",
            params,
          }),
        },
      ]}
      divider
    />
  );
}
