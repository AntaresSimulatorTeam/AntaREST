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

import { Box, Link as MuiLink, Tab, Tabs, type LinkProps } from "@mui/material";
import { forwardRef, useMemo } from "react";
import { Link, matchPath, Outlet, useLocation } from "react-router-dom";
import type { StudyMetadata } from "../../../../types/types";

const LinkComponent = forwardRef<HTMLAnchorElement, LinkProps & { href: string }>(
  function LinkComponent({ href, ...rest }, ref) {
    return <MuiLink {...rest} component={Link} to={href} ref={ref} />;
  },
);

interface TabItem {
  label: string;
  path: string;
  disabled?: boolean;
}

interface Props {
  study: StudyMetadata | undefined;
  tabList: TabItem[];
  divider?: boolean;
  disablePadding?: boolean;
}

function TabWrapper({ study, tabList, divider, disablePadding = false }: Props) {
  const location = useLocation();

  const selectedTab = useMemo(() => {
    const matchedTab = tabList.findIndex((tab) =>
      matchPath({ path: tab.path, end: false }, location.pathname),
    );
    return matchedTab >= 0 ? matchedTab : 0;
  }, [location.pathname, tabList]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      className="TabWrapper"
      sx={{
        width: 1,
        height: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        overflow: "auto",
      }}
    >
      <Box sx={divider ? { borderBottom: 1, borderColor: "divider" } : null}>
        <Tabs value={selectedTab}>
          {tabList.map(({ path, label, disabled }) => (
            <Tab
              key={path}
              label={label}
              disabled={disabled}
              LinkComponent={LinkComponent}
              href={path}
            />
          ))}
        </Tabs>
      </Box>
      <Box
        sx={[
          {
            flex: 1,
            p: 2,
            position: "relative",
            overflow: "auto",
            ":has(.TabsView:first-child), :has(.TabWrapper:first-child)": {
              p: 0,
            },
          },
          disablePadding && { p: 0 },
        ]}
      >
        <Outlet context={{ study }} />
      </Box>
    </Box>
  );
}

export default TabWrapper;
