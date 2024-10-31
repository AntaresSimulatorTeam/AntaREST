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

import { useTranslation } from "react-i18next";

import { SvgIconComponent } from "@mui/icons-material";
import LiveHelpRoundedIcon from "@mui/icons-material/LiveHelpRounded";
import { Box } from "@mui/material";

export interface EmptyViewProps {
  title?: string;
  icon?: SvgIconComponent;
}

function EmptyView(props: EmptyViewProps) {
  const { title, icon: Icon = LiveHelpRoundedIcon } = props;
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
      }}
    >
      {Icon && <Icon sx={{ height: 100, width: 100 }} />}
      <div>{title || t("common.noContent")}</div>
    </Box>
  );
}

export default EmptyView;
