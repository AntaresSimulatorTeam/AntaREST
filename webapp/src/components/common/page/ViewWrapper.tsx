/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
}

function ViewWrapper({ children }: ViewWrapperProps) {
  return (
    <Paper
      className="ViewWrapper"
      sx={{
        width: 1,
        height: 1,
        p: 2,
        ":has(.TabsView:first-child), :has(.TabWrapper:first-child)": {
          pt: 0,
        },
        overflow: "auto",
      }}
    >
      {children}
    </Paper>
  );
}

export default ViewWrapper;
