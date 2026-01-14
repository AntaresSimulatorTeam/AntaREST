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

import { directoryQueries } from "@/queries/directories/queries";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters } from "@/redux/selectors";
import { Box, Typography } from "@mui/material";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { useSuspenseQuery } from "@tanstack/react-query";
import * as R from "ramda";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import ManagedTreeNode from "./ManagedTreeNode";
import type { ManagedTreeProps } from "./types";
import { buildDirectoryTree, getDirectoryPath } from "./utils";

function ManagedTree({ studies, onNodeClick }: ManagedTreeProps) {
  const { t } = useTranslation();
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);

  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  const directoryTree = useMemo(() => buildDirectoryTree(directories), [directories]);

  const expandedItems = useMemo(
    () => (folder ? getDirectoryPath(directoryTree, folder) : []),
    [directoryTree, folder],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // Empty state
  // TODO: handle desktop mode - it may not require an empty state
  if (directories.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {t("studies.tree.noDirectories", {
            defaultValue: "No directories found",
          })}
        </Typography>
      </Box>
    );
  }

  return (
    <SimpleTreeView defaultExpandedItems={expandedItems} defaultSelectedItems={folder}>
      <ManagedTreeNode node={directoryTree} onNodeClick={onNodeClick} selectedPath={folder} />
    </SimpleTreeView>
  );
}

export default ManagedTree;
