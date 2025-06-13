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

import { Paper, type SxProps, type Theme } from "@mui/material";

interface FlexConfig {
  direction?: "row" | "column";
  gap?: number;
}

export interface ViewWrapperProps {
  children: React.ReactNode;
  flex?: boolean | FlexConfig;
  disablePadding?: boolean;
}

function ViewWrapper({ children, flex = false, disablePadding = false }: ViewWrapperProps) {
  const getFlexStyles = (): SxProps<Theme> | null => {
    if (!flex) {
      return null;
    }

    const config: FlexConfig = typeof flex === "boolean" ? {} : flex;

    return {
      display: "flex",
      flexDirection: config.direction || "column",
      gap: config.gap,
    };
  };

  const baseStyles: SxProps<Theme> = {
    width: 1,
    height: 1,
    p: disablePadding ? 0 : 2,
    overflow: flex ? "hidden" : "auto",
    position: "relative",
    borderRadius: 0,
    // Remove padding for components that manage their own padding
    ":has(.TabsView:first-child), :has(.TabWrapper:first-child)": {
      p: 0,
    },
  };

  const flexStyles = getFlexStyles();

  return (
    <Paper className="ViewWrapper" sx={flexStyles ? { ...baseStyles, ...flexStyles } : baseStyles}>
      {children}
    </Paper>
  );
}

export default ViewWrapper;
