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

import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import HomeIcon from "@mui/icons-material/Home";
import {
  alpha,
  Box,
  Collapse,
  IconButton,
  Stack,
  type SxProps,
  type Theme,
  Tooltip,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

type TreeSectionVariant = "managed" | "external";

interface TreeSectionProps {
  variant: TreeSectionVariant;
  title: string;
  subtitle?: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  onAddDirectory?: () => void;
  onRootClick?: () => void;
}

const variantStyles: Record<
  TreeSectionVariant,
  {
    container: SxProps<Theme>;
    icon: SxProps<Theme>;
    title: SxProps<Theme>;
    subtitle?: SxProps<Theme>;
  }
> = {
  managed: {
    container: {
      backgroundColor: (theme) => `${theme.palette.info.main}08`,
      borderLeft: (theme) => `3px solid ${theme.palette.info.main}`,
      p: 0.5,
    },
    icon: {
      display: "flex",
      alignItems: "center",
      color: "info.main",
      fontSize: 18,
    },
    title: {
      color: "info.main",
      fontWeight: 600,
      textTransform: "uppercase",
      letterSpacing: 0.5,
    },
  },
  external: {
    container: {
      backgroundColor: (theme) => alpha(theme.palette.action.disabled, 0.05),
      borderLeft: (theme) => `3px solid ${theme.palette.action.disabled}`,
      p: 0.5,
    },
    icon: {
      display: "flex",
      alignItems: "center",
      color: "text.secondary",
      fontSize: 18,
    },
    title: {
      color: "text.secondary",
      fontWeight: 600,
      textTransform: "uppercase",
      letterSpacing: 0.5,
    },
  },
};

function TreeSection({
  variant,
  title,
  icon,
  children,
  onAddDirectory,
  onRootClick,
}: TreeSectionProps) {
  const styles = variantStyles[variant];
  const { t } = useTranslation();
  const [isCollapsed, setIsCollapsed] = useState(false);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={styles.container}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Stack
          direction="row"
          spacing={1}
          alignItems="center"
          onClick={() => setIsCollapsed((prev) => !prev)}
          sx={{ cursor: "pointer" }}
        >
          <Box sx={styles.icon}>{icon}</Box>
          <Typography variant="subtitle2" sx={styles.title}>
            {title}
          </Typography>
        </Stack>
        <Stack direction="row">
          {onAddDirectory && (
            <Tooltip title={t("studies.tree.addRootDirectory")} placement="top" arrow>
              <IconButton
                size="small"
                onClick={onAddDirectory}
                sx={{ p: 0.5 }}
                aria-label="Create new folder"
              >
                <CreateNewFolderIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Tooltip>
          )}
          {onRootClick && (
            <IconButton size="small" onClick={onRootClick} sx={{ p: 0.5 }} aria-label="Home">
              <HomeIcon sx={{ fontSize: 18 }} />
            </IconButton>
          )}
        </Stack>
      </Stack>
      <Collapse in={!isCollapsed}>{children}</Collapse>
    </Box>
  );
}

export default TreeSection;
