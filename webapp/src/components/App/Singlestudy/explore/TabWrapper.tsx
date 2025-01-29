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

import { useEffect, useState } from "react";
import { styled, Tabs, Tab, Box, type SxProps, type Theme } from "@mui/material";
import { Outlet, matchPath, useLocation, useNavigate } from "react-router-dom";
import type { StudyMetadata } from "../../../../types/types";
import { mergeSxProp } from "../../../../utils/muiUtils";

export const StyledTabs = styled(Tabs, {
  shouldForwardProp: (prop) => prop !== "border" && prop !== "tabStyle",
})<{ border?: boolean; tabStyle?: "normal" | "withoutBorder" }>(({ theme, border, tabStyle }) => ({
  width: "98%",
  height: "50px",
  ...(border === true && {
    borderBottom: 1,
    borderColor: "divider",
  }),
  ...(tabStyle &&
    tabStyle === "withoutBorder" && {
      "& .MuiTabs-indicator": {
        display: "none",
      },
    }),
}));

interface TabItem {
  label: string;
  path: string;
  onClick?: () => void;
  disabled?: boolean;
}

interface Props {
  study: StudyMetadata | undefined;
  tabList: TabItem[];
  border?: boolean;
  tabStyle?: "normal" | "withoutBorder";
  sx?: SxProps<Theme>;
}

function TabWrapper({ study, tabList, border, tabStyle, sx }: Props) {
  const location = useLocation();
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState(0);

  useEffect(() => {
    const matchedTab = tabList.findIndex((tab) =>
      matchPath({ path: tab.path, end: false }, location.pathname),
    );
    setSelectedTab(matchedTab >= 0 ? matchedTab : 0);
  }, [location.pathname, tabList]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
    navigate(tabList[newValue].path);
    tabList[newValue].onClick?.();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      className="TabWrapper"
      sx={mergeSxProp(
        {
          width: 1,
          height: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-start",
          overflow: "auto",
        },
        sx,
      )}
    >
      <Box sx={border ? { borderBottom: 1, borderColor: "divider" } : null}>
        <StyledTabs
          border={border}
          tabStyle={tabStyle}
          value={selectedTab}
          onChange={handleChange}
          variant="scrollable"
        >
          {tabList.map((tab) => (
            <Tab key={tab.path} label={tab.label} disabled={tab.disabled} wrapped />
          ))}
        </StyledTabs>
      </Box>
      <Outlet context={{ study }} />
    </Box>
  );
}

export default TabWrapper;
