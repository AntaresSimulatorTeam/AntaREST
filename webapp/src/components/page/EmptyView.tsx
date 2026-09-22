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

import type { SvgIconComponent } from "@mui/icons-material";
import LiveHelpRoundedIcon from "@mui/icons-material/LiveHelpRounded";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

export interface EmptyViewProps {
  title?: string;
  icon?: SvgIconComponent;
  primaryActions?: React.ReactNode;
  secondaryActions?: React.ReactNode;
}

function EmptyView({
  title,
  icon: Icon = LiveHelpRoundedIcon,
  primaryActions,
  secondaryActions,
}: EmptyViewProps) {
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        height: 1,
        width: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
      }}
    >
      {secondaryActions && (
        <Box
          sx={{
            display: "flex",
            gap: 1,
            position: "absolute",
            top: 0,
            right: 0,
          }}
        >
          {secondaryActions}
        </Box>
      )}
      {Icon && <Icon sx={{ height: 100, width: 100, color: "text.disabled" }} />}
      <Typography color="textDisabled">{title || t("common.noContent")}</Typography>
      {primaryActions && <Box sx={{ display: "flex", gap: 1, m: 2 }}>{primaryActions}</Box>}
    </Box>
  );
}

export default EmptyView;
