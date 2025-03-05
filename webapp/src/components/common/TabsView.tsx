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

import { TabContext, TabList, TabPanel, type TabListProps } from "@mui/lab";
import { Box, Tab } from "@mui/material";
import { useState } from "react";

interface TabsViewProps {
  items: Array<{
    label: string;
    content: React.FunctionComponent;
  }>;
  onChange?: TabListProps["onChange"];
  divider?: boolean;
}

function TabsView({ items, onChange, divider }: TabsViewProps) {
  const [value, setValue] = useState("0");

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newValue: string) => {
    setValue(newValue);
    onChange?.(event, newValue);
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
        height: 1,
      }}
    >
      <TabContext value={value}>
        {/* Don't set divider to `TabList`, this causes issue with `variant="scrollable"` */}
        <Box sx={divider ? { borderBottom: 1, borderColor: "divider" } : null}>
          <TabList variant="scrollable" onChange={handleChange}>
            {items.map(({ label }, index) => (
              <Tab key={index} label={label} value={index.toString()} wrapped />
            ))}
          </TabList>
        </Box>
        {items.map(({ content: Content }, index) => (
          <TabPanel
            key={index}
            value={index.toString()}
            sx={{ px: 0, pb: 0, pt: 2, height: 1, overflow: "auto" }}
          >
            <Content />
          </TabPanel>
        ))}
      </TabContext>
    </Box>
  );
}

export default TabsView;
