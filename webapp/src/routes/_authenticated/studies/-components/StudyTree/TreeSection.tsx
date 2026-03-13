/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import CustomScrollbar from "@/components/CustomScrollbar";
import { useScrollRestoration } from "@/hooks/useScrollRestoration";
import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import HomeIcon from "@mui/icons-material/Home";
import { Box, IconButton, Stack, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import {
  contentSxOverride,
  ICON_BUTTON_PADDING,
  ICON_SIZE,
  innerContentSx,
  scrollbarStyle,
  titleStyles,
  variantStyles,
} from "./styles";

export type TreeSectionVariant = "managed" | "external";

interface Props {
  variant: TreeSectionVariant;
  title: string;
  icon: React.ReactNode;
  onToggleCollapse: () => void;
  onAddDirectory?: () => void;
  onRootClick?: () => void;
  /** sessionStorage key used to persist and restore scroll position across navigations. */
  scrollKey?: string;
  children: React.ReactNode;
}

function TreeSection({
  variant,
  title,
  icon,
  onToggleCollapse,
  onAddDirectory,
  onRootClick,
  scrollKey,
  children,
}: Props) {
  const { container, iconColor, titleColor } = variantStyles[variant];
  const { t } = useTranslation();
  const scrollEvents = useScrollRestoration(scrollKey);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {/* Header row */}
      <Box sx={container}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Stack
            direction="row"
            spacing={1}
            alignItems="center"
            onClick={onToggleCollapse}
            sx={{ cursor: "pointer" }}
          >
            <Box sx={{ color: iconColor, fontSize: ICON_SIZE, lineHeight: 0 }}>{icon}</Box>
            <Typography variant="subtitle2" sx={[titleStyles, { color: titleColor }]}>
              {title}
            </Typography>
          </Stack>

          <Stack direction="row">
            {onAddDirectory && (
              <Tooltip title={t("studies.tree.addRootDirectory")} placement="top" arrow>
                <IconButton
                  size="small"
                  onClick={onAddDirectory}
                  sx={{ p: ICON_BUTTON_PADDING }}
                  aria-label="Create new folder"
                >
                  <CreateNewFolderIcon sx={{ fontSize: ICON_SIZE }} />
                </IconButton>
              </Tooltip>
            )}
            {onRootClick && (
              <IconButton
                size="small"
                onClick={onRootClick}
                sx={{ p: ICON_BUTTON_PADDING }}
                aria-label="Home"
              >
                <HomeIcon sx={{ fontSize: ICON_SIZE }} />
              </IconButton>
            )}
          </Stack>
        </Stack>
      </Box>

      {/* Content row — collapses via 0fr grid row in parent */}
      <Box sx={[container, contentSxOverride]}>
        <Box sx={innerContentSx}>
          <CustomScrollbar style={scrollbarStyle} events={scrollEvents}>
            {children}
          </CustomScrollbar>
        </Box>
      </Box>
    </>
  );
}

export default TreeSection;
