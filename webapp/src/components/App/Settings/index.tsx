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

import SettingsIcon from "@mui/icons-material/Settings";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import { Box, Tab } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import RootPage from "../../common/page/RootPage";
import Groups from "./Groups";
import Maintenance from "./Maintenance";
import Tokens from "./Tokens";
import Users from "./Users";
import General from "./General";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { isAuthUserAdmin, isAuthUserInGroupAdmin } from "../../../redux/selectors";
import { tuple } from "../../../utils/tsUtils";

function Settings() {
  const [tabValue, setTabValue] = useState("1");
  const [t] = useTranslation();
  const isUserAdmin = useAppSelector(isAuthUserAdmin);
  const isUserInGroupAdmin = useAppSelector(isAuthUserInGroupAdmin);

  const tabList = useMemo(() => {
    return [
      tuple(t("global.general"), () => <General />),
      isUserAdmin && tuple(t("global.users"), () => <Users />),
      (isUserAdmin || isUserInGroupAdmin) && tuple(t("global.group"), () => <Groups />),
      tuple(t("global.tokens"), () => <Tokens />),
      isUserAdmin && tuple(t("global.maintenance"), () => <Maintenance />),
    ].filter(Boolean);
  }, [isUserAdmin, isUserInGroupAdmin, t]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setTabValue(newValue);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabContext value={tabValue}>
      <RootPage
        title={t("global.settings")}
        titleIcon={SettingsIcon}
        headerBottom={
          <Box
            sx={{
              width: 1,
              borderBottom: 1,
              borderColor: "divider",
            }}
          >
            <TabList onChange={handleTabChange}>
              {tabList.map(([label], index) => (
                <Tab key={label} label={label} value={String(index + 1)} />
              ))}
            </TabList>
          </Box>
        }
        hideHeaderDivider
      >
        {tabList.map(([label, Element], index) => (
          <TabPanel
            sx={{
              paddingTop: 0,
              paddingBottom: 0,
              overflow: "auto",
            }}
            key={label}
            value={String(index + 1)}
          >
            <Element />
          </TabPanel>
        ))}
      </RootPage>
    </TabContext>
  );
}

export default Settings;
