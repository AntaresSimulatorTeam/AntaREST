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

import { Box, Collapse, List, ListSubheader } from "@mui/material";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useState } from "react";

export interface ListCollapseProps {
  title?: string;
  titleIcon?: React.ReactNode;
  defaultOpen?: boolean;
  children?: React.ReactNode;
}

function ListCollapse({ title, titleIcon, defaultOpen = true, children }: ListCollapseProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <List
      subheader={
        <ListSubheader
          sx={{ display: "flex", alignItems: "center", cursor: "pointer" }}
          onClick={() => setOpen(!open)}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, flex: 1 }}>
            {titleIcon}
            {title}
          </Box>
          {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </ListSubheader>
      }
      disablePadding
    >
      <Collapse in={open}>{children}</Collapse>
    </List>
  );
}

export default ListCollapse;
