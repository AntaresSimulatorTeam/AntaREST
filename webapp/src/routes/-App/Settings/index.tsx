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
import About from "@/routes/-App/Settings/About";
import SettingsIcon from "@mui/icons-material/Settings";
import { useTranslation } from "react-i18next";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { isAuthUserAdmin, isAuthUserInGroupAdmin } from "../../../redux/selectors";
import General from "./General";
import Groups from "./Groups";
import Maintenance from "./Maintenance";
import Tokens from "./Tokens";
import Users from "./Users";

function Settings() {
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
              content: <General />,
            },
            isUserAdmin && {
              label: t("global.users"),
              content: <Users />,
            },
            (isUserAdmin || isUserInGroupAdmin) && {
              label: t("global.group"),
              content: <Groups />,
            },
            isWebMode && {
              label: t("global.tokens"),
              content: <Tokens />,
            },
            isUserAdmin && {
              label: t("global.maintenance"),
              content: <Maintenance />,
            },
            {
              label: t("global.about"),
              content: <About />,
            },
          ].filter(Boolean)}
        />
      </ViewWrapper>
    </RootPage>
  );
}

export default Settings;
