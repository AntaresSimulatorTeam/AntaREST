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

import { Box, Button, type SxProps, type Theme } from "@mui/material";
import SearchFE from "./fieldEditors/SearchFE";
import { mergeSxProp } from "../../utils/muiUtils";
import AddIcon from "@mui/icons-material/Add";
import { useTranslation } from "react-i18next";

interface PropsType {
  topContent?: React.ReactNode;
  mainContent: React.ReactNode | undefined;
  secondaryContent?: React.ReactNode;
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
          pt: 1,
        },
        sx,
      )}
    >
      {onSearchFilterChange && (
        <SearchFE onSearchValueChange={onSearchFilterChange} size="extra-small" sx={{ px: 1 }} />
      )}
      {onAdd && (
        <Box sx={{ display: "flex", px: 1, my: 1 }}>
          <Button
            color="primary"
            variant="contained"
            startIcon={<AddIcon />}
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
