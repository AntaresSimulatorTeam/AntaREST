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

import BackButton from "@/components/buttons/BackButton";
import type { RoutePaths } from "@/router";
import { buildKey } from "@/utils/reactUtils";
import { TabContext, TabList, TabPanel, type TabListProps } from "@mui/lab";
import { Box, Tab } from "@mui/material";
import { Link, Outlet, useLocation } from "@tanstack/react-router";
import { useState } from "react";

interface BaseTab {
  label: string;
  disabled?: boolean;
}

interface RouteTab extends BaseTab {
  to: RoutePaths;
  content?: never;
}

interface ContentTab extends BaseTab {
  content: React.ReactNode;
  to?: never;
}

interface TabsViewProps {
  items: RouteTab[] | ContentTab[];
  onChange?: TabListProps["onChange"];
  onBack?: VoidFunction;
  divider?: boolean;
  disablePadding?: boolean;
  disableGutters?: boolean;
}

function isRouteTabs(tabs: RouteTab[] | ContentTab[]): tabs is RouteTab[] {
  const firstTab = tabs[0];
  return !!firstTab && "to" in firstTab && typeof firstTab.to === "string";
}

function TabsView({
  items,
  onChange,
  onBack,
  divider = false,
  disablePadding = false,
  disableGutters = false,
}: TabsViewProps) {
  const { pathname } = useLocation();
  const [currentTabIndex, setCurrentTabIndex] = useState(0);

  const hasRouteTabs = isRouteTabs(items);
  const currentTabValue = hasRouteTabs
    ? items.find(({ to }) => pathname === to || pathname.startsWith(to + "/"))?.to || ""
    : currentTabIndex;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    if (!hasRouteTabs) {
      setCurrentTabIndex(newValue);
    }
    onChange?.(event, newValue);
  };

  ////////////////////////////////////////////////////////////////
  // Tab
  ////////////////////////////////////////////////////////////////

  const getTabKey = (itemIndex: number) => {
    return hasRouteTabs ? items[itemIndex].to : buildKey(items[itemIndex].label, itemIndex);
  };

  const getTabValue = (itemIndex: number) => {
    return hasRouteTabs ? items[itemIndex].to : itemIndex;
  };

  const getTabProps = (itemIndex: number) => {
    if (hasRouteTabs) {
      return {
        value: getTabValue(itemIndex),
        LinkComponent: Link,
        href: items[itemIndex].to,
      };
    }

    return { value: getTabValue(itemIndex) };
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      className="TabsView"
      sx={{
        display: "flex",
        flexDirection: "column",
        width: 1,
        height: 1,
      }}
    >
      <TabContext value={currentTabValue}>
        <Box
          sx={[
            !!onBack && { display: "flex" },
            divider && { borderBottom: 1, borderColor: "divider" },
          ]}
        >
          {onBack && <BackButton onClick={onBack} />}
          <TabList onChange={handleChange}>
            {items.map((item, index) => (
              <Tab
                key={getTabKey(index)}
                label={item.label}
                disabled={item.disabled}
                {...getTabProps(index)}
              />
            ))}
          </TabList>
        </Box>
        {items.map((item, index) => (
          <TabPanel
            key={getTabKey(index)}
            value={getTabValue(index)}
            sx={[
              {
                flex: 1,
                p: 2,
                position: "relative",
                overflow: "auto",
                ":has(> .TabsView:first-child), :has(> .TabWrapper:first-child), :has(> .SplitView:first-child)":
                  {
                    p: 0,
                  },
              },
              disablePadding && { p: 0 },
              disableGutters && { px: 0 },
            ]}
          >
            {hasRouteTabs ? <Outlet /> : item.content}
          </TabPanel>
        ))}
      </TabContext>
    </Box>
  );
}

export default TabsView;
