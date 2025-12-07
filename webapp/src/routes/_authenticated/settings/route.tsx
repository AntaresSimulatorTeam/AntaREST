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

import RootPage from "@/components/page/RootPage";
import ViewWrapper from "@/components/page/ViewWrapper";
import TabsView from "@/components/TabsView";
import { useAppMode } from "@/hooks/useAppMode";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { isAuthUserAdmin, isAuthUserInGroupAdmin } from "@/redux/selectors";
import SettingsIcon from "@mui/icons-material/Settings";
import { createFileRoute } from "@tanstack/react-router";
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
      <ViewWrapper>
        <TabsView
          items={[
            {
              label: t("global.general"),
              to: "/settings/general" as const,
            },
            isUserAdmin && {
              label: t("global.users"),
              to: "/settings/users" as const,
            },
            (isUserAdmin || isUserInGroupAdmin) && {
              label: t("global.group"),
              to: "/settings/groups" as const,
            },
            isWebMode && {
              label: t("global.tokens"),
              to: "/settings/tokens" as const,
            },
            isUserAdmin && {
              label: t("global.maintenance"),
              to: "/settings/maintenance" as const,
            },
            {
              label: t("global.about"),
              to: "/settings/about" as const,
            },
          ].filter(Boolean)}
        />
      </ViewWrapper>
    </RootPage>
  );
}
