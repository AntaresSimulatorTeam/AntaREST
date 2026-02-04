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
  Box,
  IconButton,
  Stack,
  type SxProps,
  type Theme,
  Tooltip,
  Typography,
} from "@mui/material";
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
      backgroundColor: "action.hover",
      borderLeft: (theme) => `3px solid ${theme.palette.action.disabled}`,
      p: 0.5,
    },
    icon: {
      color: "text.secondary",
      fontSize: 18,
    },
    title: {
      color: "text.secondary",
      fontWeight: 600,
      textTransform: "uppercase",
      letterSpacing: 0.5,
    },
    subtitle: {
      color: "text.disabled",
      fontStyle: "italic",
    },
  },
};

function TreeSection({
  variant,
  title,
  subtitle,
  icon,
  children,
  onAddDirectory,
  onRootClick,
}: TreeSectionProps) {
  const styles = variantStyles[variant];
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={styles.container}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Box sx={styles.icon}>{icon}</Box>
          <Typography variant="subtitle2" sx={styles.title}>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" sx={styles.subtitle}>
              {subtitle}
            </Typography>
          )}
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
            <Tooltip
              title={t("studies.tree.allStudies", { defaultValue: "All studies" })} // TODO: update label and add key
              placement="top"
              arrow
            >
              <IconButton
                size="small"
                onClick={onRootClick}
                sx={{ p: 0.5 }}
                aria-label="All studies"
              >
                <HomeIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Tooltip>
          )}
        </Stack>
      </Stack>
      {children}
    </Box>
  );
}

export default TreeSection;
