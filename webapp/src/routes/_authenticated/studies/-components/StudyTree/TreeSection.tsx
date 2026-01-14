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

import { Box, Stack, type SxProps, type Theme, Typography } from "@mui/material";

type TreeSectionVariant = "managed" | "external";

interface TreeSectionProps {
  variant: TreeSectionVariant;
  title: string;
  subtitle?: string;
  icon: React.ReactNode;
  children: React.ReactNode;
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
      color: (theme) => theme.palette.info.main,
      fontSize: 20,
    },
    title: {
      color: (theme) => theme.palette.info.main,
      fontWeight: 600,
      textTransform: "uppercase",
      letterSpacing: 0.5,
    },
  },
  external: {
    container: {
      backgroundColor: (theme) => theme.palette.action.hover,
      borderLeft: (theme) => `3px solid ${theme.palette.action.disabled}`,
      p: 0.5,
    },
    icon: {
      color: (theme) => theme.palette.text.secondary,
      fontSize: 20,
    },
    title: {
      color: (theme) => theme.palette.text.secondary,
      fontWeight: 600,
      textTransform: "uppercase",
      letterSpacing: 0.5,
    },
    subtitle: {
      color: (theme) => theme.palette.text.disabled,
      fontStyle: "italic",
    },
  },
};

export default function TreeSection({
  variant,
  title,
  subtitle,
  icon,
  children,
}: TreeSectionProps) {
  const styles = variantStyles[variant];

  return (
    <Box sx={styles.container}>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
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
      {children}
    </Box>
  );
}
