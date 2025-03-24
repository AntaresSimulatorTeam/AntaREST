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

import { Paper } from "@mui/material";

export interface ViewWrapperProps {
  children: React.ReactNode;
  flex?:
    | boolean
    | {
        direction?: "row" | "column";
        gap?: number;
      };
  disablePadding?: boolean;
}

function ViewWrapper({ children, flex = false, disablePadding = false }: ViewWrapperProps) {
  const flexObj = typeof flex === "boolean" ? {} : flex;
  const flexValues = { flexDirection: flexObj.direction || "column", gap: flexObj.gap };

  return (
    <Paper
      className="ViewWrapper"
      sx={[
        {
          width: 1,
          height: 1,
          p: 2,
          // <TabsView> and <TabWrapper> have their own padding
          ":has(.TabsView:first-child), :has(.TabWrapper:first-child)": {
            p: 0,
          },
          overflow: "auto",
          position: "relative",
          borderRadius: 0,
        },
        flex && { display: "flex", ...flexValues },
        disablePadding && { p: 0 },
      ]}
    >
      {children}
    </Paper>
  );
}

export default ViewWrapper;
