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

import { ReactNode } from "react";

import { Box, Divider, SxProps, Theme } from "@mui/material";

interface Props {
  left: ReactNode;
  right: ReactNode;
  sx?: SxProps<Theme>;
}

/**
 * Renders a split layout view with a fixed left column and a flexible right column.
 * This component is deprecated and should be replaced with the `SplitView` component for enhanced functionality and flexibility.
 *
 * @deprecated Use `SplitView` instead for better layout management and customization options.
 *
 * @param props - The component props including `left` and `right` components to render in the split layout, and `sx` for styling.
 * @returns A React component that displays a split layout with left and right sections.
 */
function SplitLayoutView(props: Props) {
  const { left, right, sx } = props;

  return (
    <Box
      width="100%"
      display="flex"
      justifyContent="space-evenly"
      alignItems="center"
      overflow="hidden"
      flexGrow="1"
      sx={sx}
    >
      <Box
        className="SplitLayoutView__Left"
        width="20%"
        height="100%"
        position="relative"
        sx={{
          px: 2,
        }}
      >
        {left}
      </Box>
      <Divider
        sx={{ width: "1px", height: "96%" }}
        orientation="vertical"
        variant="middle"
      />
      <Box
        className="SplitLayoutView__Right"
        width="calc(80% - 1px)"
        height="96%"
        display="flex"
        justifyContent="center"
        alignItems="flex-start"
        position="relative"
        overflow="hidden"
        sx={{
          px: 2,
        }}
      >
        {right}
      </Box>
    </Box>
  );
}

export default SplitLayoutView;
