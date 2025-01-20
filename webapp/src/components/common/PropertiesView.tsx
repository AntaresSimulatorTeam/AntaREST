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

import { ReactNode } from "react";
import { Box, Button, SxProps, Theme } from "@mui/material";
import SearchFE from "./fieldEditors/SearchFE";
import { mergeSxProp } from "../../utils/muiUtils";
import { Add } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

interface PropsType {
  topContent?: ReactNode;
  mainContent: ReactNode | undefined;
  secondaryContent?: ReactNode;
  onSearchFilterChange?: (value: string) => void;
  onAdd?: () => void;
  sx?: SxProps<Theme>;
}

function PropertiesView({
  onAdd,
  onSearchFilterChange,
  topContent,
  mainContent,
  secondaryContent,
  sx,
}: PropsType) {
  const { t } = useTranslation();

  return (
    <Box
      sx={mergeSxProp(
        {
          width: 1,
          height: 1,
          display: "flex",
          flexDirection: "column",
        },
        sx,
      )}
    >
      {onSearchFilterChange && (
        <SearchFE onSearchValueChange={onSearchFilterChange} />
      )}
      {onAdd && (
        <Box sx={{ display: "flex", px: 1, my: 1 }}>
          <Button
            color="primary"
            variant="contained"
            size="small"
            startIcon={<Add />}
            onClick={onAdd}
            sx={{
              display: "flex",
              justifyContent: "flex-start",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {t("global.add")}
          </Button>
        </Box>
      )}
      {topContent}
      {mainContent}
      {secondaryContent}
    </Box>
  );
}

export default PropertiesView;
