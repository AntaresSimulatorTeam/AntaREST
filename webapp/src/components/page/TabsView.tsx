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
import { TabContext, TabList, TabPanel, type TabListProps } from "@mui/lab";
import { Box, Tab } from "@mui/material";
import {
  Outlet,
  useMatchRoute,
  useRouter,
  type RegisteredRouter,
  type ToOptions,
} from "@tanstack/react-router";
import { useState } from "react";
import RouterLink from "../router/RouterLink";

interface BaseTab {
  label: string;
  disabled?: boolean;
  // Optional ID to use as tab value instead of generated one.
  // Useful with content tabs to have a stable tab value across renders when tab order can change.
  // Also used in `renderPanel()` callback to identify the tab.
  id?: string;
}

interface RouteTab extends BaseTab {
  linkOptions: ToOptions;
  content?: never;
}

interface ContentTab extends BaseTab {
  linkOptions?: never;
  content?: React.ReactNode;
}

export interface TabsViewProps<
  TTabs extends RouteTab[] | ContentTab[] = RouteTab[] | ContentTab[],
> {
  tabs: TTabs;
  onChange?: TabListProps["onChange"];
  onBack?: VoidFunction;
  renderPanel?: (props: { children: React.ReactNode }, tab: TTabs[number]) => React.ReactNode;
  divider?: boolean;
  disablePadding?: boolean;
  disableGutters?: boolean;
}

function isRouteTab(tab: RouteTab | ContentTab): tab is RouteTab {
  return !!tab?.linkOptions;
}

function isRouteTabs(tabs: RouteTab[] | ContentTab[]): tabs is RouteTab[] {
  return tabs.length > 0 && isRouteTab(tabs[0]);
}

function getRouteTabValue(tab: RouteTab, router: RegisteredRouter) {
  return tab.id ?? router.buildLocation(tab.linkOptions).href;
}

function getContentTabValue(tab: ContentTab, tabIndex: number) {
  return tab.id ?? tabIndex;
}

function getTabValue(tab: RouteTab | ContentTab, tabIndex: number, router: RegisteredRouter) {
  return isRouteTab(tab) ? getRouteTabValue(tab, router) : getContentTabValue(tab, tabIndex);
}

function TabsView<TTabs extends RouteTab[] | ContentTab[]>({
  tabs,
  onChange,
  onBack,
  renderPanel = ({ children }) => children,
  divider = false,
  disablePadding = false,
  disableGutters = false,
}: TabsViewProps<TTabs>) {
  const router = useRouter();
  const matchRoute = useMatchRoute();
  const hasRouteTabs = isRouteTabs(tabs);

  const [activeContentTabValue, setActiveContentTabValue] = useState(() =>
    tabs.length > 0 ? getTabValue(tabs[0], 0, router) : "",
  );

  const activeRouteTab = hasRouteTabs
    ? tabs.find((tab) => matchRoute({ ...tab.linkOptions, fuzzy: true }))
    : undefined;

  const activeTabValue = activeRouteTab
    ? getRouteTabValue(activeRouteTab, router)
    : activeContentTabValue;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newTabIndex: number) => {
    if (!hasRouteTabs) {
      const newTabValue = getContentTabValue(tabs[newTabIndex], newTabIndex);
      setActiveContentTabValue(newTabValue);
    }
    onChange?.(event, newTabIndex);
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
      <TabContext value={activeTabValue}>
        <Box
          sx={[
            !!onBack && { display: "flex" },
            divider && { borderBottom: 1, borderColor: "divider" },
          ]}
        >
          {onBack && <BackButton onClick={onBack} />}
          <TabList onChange={handleChange}>
            {tabs.map((tab, index) => {
              const value = getTabValue(tab, index, router);

              return (
                <Tab
                  key={value}
                  value={value}
                  label={tab.label}
                  disabled={tab.disabled}
                  {...(isRouteTab(tab)
                    ? {
                        component: RouterLink,
                        // ⚠️ Providing `href` gives the same link on all <a href /> elements
                        ...tab.linkOptions,
                      }
                    : {})}
                />
              );
            })}
          </TabList>
        </Box>
        {tabs.map((tab, index) => {
          const value = getTabValue(tab, index, router);

          return (
            <TabPanel
              key={value}
              value={value}
              sx={[
                {
                  flex: 1,
                  p: 2,
                  position: "relative",
                  overflow: "auto",
                  ":has(> :first-child:is(.TabsView, .SplitView, .ViewWrapper))": {
                    p: 0,
                  },
                },
                disablePadding && { p: 0 },
                disableGutters && { px: 0 },
              ]}
            >
              {renderPanel({ children: hasRouteTabs ? <Outlet /> : tab.content }, tab)}
            </TabPanel>
          );
        })}
      </TabContext>
    </Box>
  );
}

export default TabsView;
