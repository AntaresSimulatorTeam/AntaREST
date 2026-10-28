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

interface Props {
  children: React.ReactNode;
  destination: React.ReactNode;
}

function StudyDestinationLayout({ children, destination }: Props) {
  const { t } = useTranslation();

  return (
    <CustomScrollbar style={{ flex: 1, minHeight: 0 }}>
      <Stack direction={{ xs: "column", md: "row" }} spacing={3} sx={{ height: { md: 1 } }}>
        <Box
          component={CustomScrollbar}
          sx={{ minHeight: 0, minWidth: 0, width: 1, flex: { md: 9 } }}
        >
          <Stack direction="column" spacing={2} sx={{ p: 1 }}>
            {children}
          </Stack>
        </Box>
        <Stack
          direction="column"
          spacing={2}
          sx={{
            p: 1,
            pt: { xs: 3, md: 1 },
            pl: { xs: 1, md: 3 },
            borderTopWidth: { xs: 1, md: 0 },
            borderTopStyle: "solid",
            borderLeftWidth: { xs: 0, md: 1 },
            borderLeftStyle: "solid",
            borderColor: "divider",
            minWidth: 0,
            minHeight: 0,
            height: { xs: "clamp(320px, 50dvh, 480px)", md: 1 },
            // Give the directory explorer slightly more room than the form fields.
            flex: { md: 11 },
          }}
        >
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
