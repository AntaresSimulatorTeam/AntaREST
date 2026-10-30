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
import { Box, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { destinationPanelSx, fieldsPanelSx } from "./styles";

interface Props {
  children: React.ReactNode;
  destination: React.ReactNode;
}

function StudyDestinationLayout({ children, destination }: Props) {
  const { t } = useTranslation();

  return (
    <CustomScrollbar style={{ flex: 1, minHeight: 0 }}>
      <Stack direction={{ xs: "column", md: "row" }} spacing={3} sx={{ height: { md: 1 } }}>
        <Box component={CustomScrollbar} sx={fieldsPanelSx}>
          <Stack direction="column" spacing={2} sx={{ p: 1 }}>
            {children}
          </Stack>
        </Box>
        <Stack direction="column" spacing={2} sx={destinationPanelSx}>
          <Typography component="h3" variant="subtitle2">
            {t("studies.destination")}
          </Typography>
          {destination}
        </Stack>
      </Stack>
    </CustomScrollbar>
  );
}

export default StudyDestinationLayout;
