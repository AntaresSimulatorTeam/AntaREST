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
import { Box, Typography } from "@mui/material";
import BasicPage from "./BasicPage";

interface Props {
  title: string;
  titleIcon?: SvgIconComponent;
  headerTopRight?: React.ReactNode;
  headerBottom?: React.ReactNode;
  hideHeaderDivider?: boolean;
  children?: React.ReactNode;
}

function RootPage(props: Props) {
  const { title, titleIcon, headerTopRight, headerBottom, children, hideHeaderDivider } = props;

  const TitleIcon = titleIcon as SvgIconComponent;

  return (
    <BasicPage
      header={
        <>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              mb: 1,
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                flex: 1,
              }}
            >
              {TitleIcon && (
                <TitleIcon
                  sx={{
                    color: "text.secondary",
                    width: "42px",
                    height: "42px",
                  }}
                />
              )}
              <Typography sx={{ ml: 2, fontSize: 34 }}>{title}</Typography>
            </Box>
            {headerTopRight && (
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "flex-end",
                  flex: 1,
                }}
              >
                {headerTopRight}
              </Box>
            )}
          </Box>
          {headerBottom && <Box sx={{ width: 1, mb: 1 }}>{headerBottom}</Box>}
        </>
      }
      hideHeaderDivider={hideHeaderDivider}
    >
      {children}
    </BasicPage>
  );
}

export default RootPage;
