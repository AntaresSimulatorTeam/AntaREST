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

import type { SvgIconComponent } from "@mui/icons-material";
import { Box, Typography, Toolbar, Divider } from "@mui/material";
import CustomScrollbar from "@/components/common/CustomScrollbar";

interface Props {
  title: string;
  titleIcon?: SvgIconComponent;
  headerActions?: React.ReactNode;
  children?: React.ReactNode;
}

function RootPage({ title, titleIcon: TitleIcon, headerActions, children }: Props) {
  return (
    <Box
      sx={{ height: 1, flex: 1, display: "flex", flexDirection: "column", overflowX: "auto" }}
      component="main"
    >
      {/* Header */}
      <Toolbar
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 3,
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            flex: 1,
            gap: 1.5,
          }}
        >
          {TitleIcon && (
            <TitleIcon
              sx={{
                width: 32,
                height: 32,
              }}
            />
          )}
          <Typography sx={{ fontSize: 28 }}>{title}</Typography>
        </Box>
        {headerActions && (
          <CustomScrollbar options={{ overflow: { y: "hidden" } }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
              }}
            >
              {headerActions}
            </Box>
          </CustomScrollbar>
        )}
      </Toolbar>

      <Divider />

      {/* Content */}
      <Box sx={{ flex: 1, overflow: "auto" }}>{children}</Box>
    </Box>
  );
}

export default RootPage;
