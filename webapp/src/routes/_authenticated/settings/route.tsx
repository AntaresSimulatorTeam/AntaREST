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

import RootPage from "@/components/page/RootPage";
import TabsView from "@/components/page/TabsView";
import { useAppMode } from "@/hooks/useAppMode";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { isAuthUserAdmin, isAuthUserInGroupAdmin } from "@/redux/selectors";
import SettingsIcon from "@mui/icons-material/Settings";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute("/_authenticated/settings")({
  component: SettingsLayout,
});

function SettingsLayout() {
  const { t } = useTranslation();
  const isUserAdmin = useAppSelector(isAuthUserAdmin);
  const isUserInGroupAdmin = useAppSelector(isAuthUserInGroupAdmin);
  const { isWebMode } = useAppMode();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <RootPage title={t("global.settings")} titleIcon={SettingsIcon}>
      <TabsView
        tabs={[
          {
            id: "general",
            label: t("global.general"),
            linkOptions: linkOptions({
              to: "/settings/general",
            }),
          },
          isUserAdmin && {
            id: "users",
            label: t("global.users"),
            linkOptions: linkOptions({
              to: "/settings/users",
            }),
          },
          (isUserAdmin || isUserInGroupAdmin) && {
            id: "groups",
            label: t("global.group"),
            linkOptions: linkOptions({
              to: "/settings/groups",
            }),
          },
          isWebMode && {
            id: "tokens",
            label: t("global.tokens"),
            linkOptions: linkOptions({
              to: "/settings/tokens",
            }),
          },
          isUserAdmin && {
            id: "maintenance",
            label: t("global.maintenance"),
            linkOptions: linkOptions({
              to: "/settings/maintenance",
            }),
          },
          {
            id: "about",
            label: t("global.about"),
            linkOptions: linkOptions({
              to: "/settings/about",
            }),
          },
        ].filter(Boolean)}
      />
    </RootPage>
  );
}
