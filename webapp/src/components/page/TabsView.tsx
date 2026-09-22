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

import BackButton from "@/components/buttons/BackButton";
import { TabContext, TabList, TabPanel, type TabListProps } from "@mui/lab";
import { Box, Stack, Tab, type SxProps, type Theme } from "@mui/material";
import { Outlet, useMatchRoute, type ToOptions } from "@tanstack/react-router";
import { useState } from "react";
import RouterLink from "../router/RouterLink";

interface BaseTab {
  label: string;
  disabled?: boolean;
  id: string | number;
}

interface RouteTab extends BaseTab {
  linkOptions: ToOptions;
  content?: never;
}

interface ContentTab extends BaseTab {
  linkOptions?: never;
  content?: React.ReactNode;
}

export interface TabsViewProps {
  tabs: RouteTab[] | ContentTab[];
  onChange?: TabListProps["onChange"];
  onBack?: VoidFunction | ToOptions;
  divider?: boolean;
  disablePadding?: boolean;
  disableGutters?: boolean;
  primaryActions?: React.ReactNode;
  secondaryActions?: React.ReactNode;
}

function isRouteTab(tab: RouteTab | ContentTab): tab is RouteTab {
  return !!tab?.linkOptions;
}

function isRouteTabs(tabs: RouteTab[] | ContentTab[]): tabs is RouteTab[] {
  return tabs.length > 0 && isRouteTab(tabs[0]);
}

function TabsView({
  tabs,
  onChange,
  onBack,
  divider = false,
  disablePadding = false,
  disableGutters = false,
  primaryActions,
  secondaryActions,
}: TabsViewProps) {
  const matchRoute = useMatchRoute();
  const hasRouteTabs = isRouteTabs(tabs);

  const [activeContentTabValue, setActiveContentTabValue] = useState(() =>
    tabs.length > 0 ? tabs[0].id : "",
  );

  const activeTabValue = hasRouteTabs
    ? tabs.find((tab) => matchRoute({ ...tab.linkOptions, fuzzy: true }))?.id || ""
    : activeContentTabValue;

  const panelSx: SxProps<Theme> = [
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
  ];

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newTabValue: BaseTab["id"]) => {
    if (!hasRouteTabs) {
      setActiveContentTabValue(newTabValue);
    }
    onChange?.(event, newTabValue);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Stack
      className="TabsView"
      direction="column"
      sx={{
        width: 1,
        height: 1,
      }}
    >
      <TabContext value={activeTabValue}>
        <Stack alignItems="normal" sx={[divider && { borderBottom: 1, borderColor: "divider" }]}>
          {onBack && (
            <BackButton
              {...(typeof onBack === "function" ? { onClick: onBack } : { linkOptions: onBack })}
            />
          )}
          {primaryActions && (
            <Stack spacing={1} sx={{ px: 1 }}>
              {primaryActions}
            </Stack>
          )}
          <TabList onChange={handleChange} sx={{ flex: 1 }}>
            {tabs.map((tab) => (
              <Tab
                key={tab.id}
                value={tab.id}
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
            ))}
          </TabList>
          {secondaryActions && (
            <Stack spacing={1} sx={{ pr: 1 }}>
              {secondaryActions}
            </Stack>
          )}
        </Stack>
        {hasRouteTabs ? (
          <Box sx={panelSx}>
            <Outlet />
          </Box>
        ) : (
          tabs.map((tab) => (
            <TabPanel key={tab.id} value={tab.id} sx={panelSx}>
              {tab.content}
            </TabPanel>
          ))
        )}
      </TabContext>
    </Stack>
  );
}

export default TabsView;
