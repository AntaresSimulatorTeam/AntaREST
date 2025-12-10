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
import router from "@/router";
import { buildKey } from "@/utils/reactUtils";
import { TabContext, TabList, TabPanel, type TabListProps } from "@mui/lab";
import { Box, Tab, type TabProps } from "@mui/material";
import { Link, Outlet, useLocation, type ToOptions } from "@tanstack/react-router";
import { useState } from "react";

interface BaseTab {
  label: string;
  disabled?: boolean;
}

interface RouteTab extends BaseTab {
  linkOptions: ToOptions;
  content?: never;
}

interface ContentTab extends BaseTab {
  linkOptions?: never;
  content: React.ReactNode;
}

export interface TabsViewProps {
  items: RouteTab[] | ContentTab[];
  onChange?: TabListProps["onChange"];
  onBack?: VoidFunction;
  renderPanel?: (props: { children: React.ReactNode }) => React.ReactNode;
  divider?: boolean;
  disablePadding?: boolean;
  disableGutters?: boolean;
}

function isRouteTabs(tabs: RouteTab[] | ContentTab[]): tabs is RouteTab[] {
  return !!tabs[0]?.linkOptions;
}

function buildHrefOnRouteTabs(items: RouteTab[]): Array<RouteTab & { href: string }> {
  return items.map((item) => ({
    ...item,
    href: router.buildLocation(item.linkOptions).href,
  }));
}

function TabsView({
  items,
  onChange,
  onBack,
  renderPanel = ({ children }) => children,
  divider = false,
  disablePadding = false,
  disableGutters = false,
}: TabsViewProps) {
  const location = useLocation();
  const [currentTabIndex, setCurrentTabIndex] = useState(0);

  const tabs = isRouteTabs(items) ? buildHrefOnRouteTabs(items) : items;
  const hasRouteTabs = isRouteTabs(tabs);

  const currentTabValue = hasRouteTabs
    ? tabs.find(
        ({ href }) => location.pathname === href || location.pathname.startsWith(href + "/"),
      )?.href || ""
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

  const getTabKey = (tabIndex: number) => {
    return hasRouteTabs ? tabs[tabIndex].href : buildKey(tabs[tabIndex].label, tabIndex);
  };

  const getTabValue = (tabIndex: number) => {
    return hasRouteTabs ? tabs[tabIndex].href : tabIndex;
  };

  const getTabProps = (tabIndex: number): TabProps => {
    if (hasRouteTabs) {
      return {
        value: getTabValue(tabIndex),
        LinkComponent: Link,
        // With MUI Tabs + router Link, providing `href` causes every Tab
        // to inherit the current tab `href` in the DOM, even though clicks work.
        // The router Link must be responsible for generating the href.
        ...items[tabIndex].linkOptions,
      };
    }

    return { value: getTabValue(tabIndex) };
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
            {tabs.map((tab, index) => (
              <Tab
                key={getTabKey(index)}
                label={tab.label}
                disabled={tab.disabled}
                {...getTabProps(index)}
              />
            ))}
          </TabList>
        </Box>
        {tabs.map((tab, index) => (
          <TabPanel
            key={getTabKey(index)}
            value={getTabValue(index)}
            sx={[
              {
                flex: 1,
                p: 2,
                position: "relative",
                overflow: "auto",
                ":has(> .TabsView:first-child), :has(> .TabWrapper:first-child), :has(> .SplitView:first-child), :has(> .ViewWrapper:first-child)":
                  {
                    p: 0,
                  },
              },
              disablePadding && { p: 0 },
              disableGutters && { px: 0 },
            ]}
          >
            {renderPanel({ children: hasRouteTabs ? <Outlet /> : tab.content })}
          </TabPanel>
        ))}
      </TabContext>
    </Box>
  );
}

export default TabsView;
