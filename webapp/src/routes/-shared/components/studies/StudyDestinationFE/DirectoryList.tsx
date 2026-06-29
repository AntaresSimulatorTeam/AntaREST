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

import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import FolderIcon from "@mui/icons-material/Folder";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { Directory } from "@/services/api/directories/types";
import { getDirectoryListSx, emptyStateSx, getDirectoryRowSx } from "./styles";

interface Props {
  /** Direct children of the currently browsed directory, already sorted. */
  childDirectories: Directory[];
  allDirectories: Directory[];
  onDirectoryClick: (dir: Directory) => void;
  /** Optional fixed height for the list; overrides the default 400-700px range. */
  listHeight?: number | string;
  /** When true, the list flex-grows to fill its parent. Overrides `listHeight`. */
  fillHeight?: boolean;
}

function DirectoryList({
  childDirectories,
  allDirectories,
  onDirectoryClick,
  listHeight,
  fillHeight = false,
}: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box component="ul" role="listbox" sx={getDirectoryListSx(listHeight, fillHeight)}>
      {childDirectories.length === 0 ? (
        <Box sx={emptyStateSx}>
          <Typography variant="body2" color="text.disabled" fontStyle="italic">
            {t("studies.destination.noSubDirectories")}
          </Typography>
        </Box>
      ) : (
        childDirectories.map((directory) => {
          const hasChildren = allDirectories.some((child) => child.parentId === directory.id);

          return (
            <Box
              component="li"
              key={directory.id}
              role="option"
              aria-selected={false}
              aria-label={directory.name}
              onClick={() => onDirectoryClick(directory)}
              sx={getDirectoryRowSx}
            >
              <FolderIcon sx={{ fontSize: 18, color: "info.main", flexShrink: 0 }} />

              <Typography variant="body2" noWrap sx={{ flex: 1 }}>
                {directory.name}
              </Typography>

              {hasChildren && <ChevronRightIcon sx={{ fontSize: 18 }} />}
            </Box>
          );
        })
      )}
    </Box>
  );
}

export default DirectoryList;
