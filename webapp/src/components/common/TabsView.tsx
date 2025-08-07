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

import BackButton from "@/components/common/buttons/BackButton";
import { TabContext, TabList, TabPanel, type TabListProps } from "@mui/lab";
import { Box, Tab } from "@mui/material";
import { useState } from "react";

interface TabsViewProps {
  items: Array<{
    label: string;
    content: React.FunctionComponent;
    disabled?: boolean;
  }>;
  onChange?: TabListProps["onChange"];
  onBack?: VoidFunction;
  divider?: boolean;
  disablePadding?: boolean;
  disableGutters?: boolean;
}

function TabsView({
  items,
  onChange,
  onBack,
  divider = false,
  disablePadding = false,
  disableGutters = false,
}: TabsViewProps) {
  const [value, setValue] = useState(0);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
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
        width: 1,
        height: 1,
      }}
    >
      <TabContext value={value}>
        <Box
          sx={[
            !!onBack && { display: "flex" },
            divider && { borderBottom: 1, borderColor: "divider" },
          ]}
        >
          {onBack && <BackButton onClick={onBack} />}
          <TabList onChange={handleChange}>
            {items.map(({ label, disabled }, index) => (
              <Tab key={label + index} label={label} value={index} disabled={disabled} />
            ))}
          </TabList>
        </Box>
        {items.map(({ content: Content, label }, index) => (
          <TabPanel
            key={label + index}
            value={index}
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
            <Content />
          </TabPanel>
        ))}
      </TabContext>
    </Box>
  );
}

export default TabsView;
