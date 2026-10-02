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

import RouterTreeItem from "@/components/router/RouterTreeItem";
import HomeIcon from "@mui/icons-material/Home";
import { Box, Tooltip } from "@mui/material";
import { useParams } from "@tanstack/react-router";
import {
  getTreeItemIcon,
  getTreeItemType,
  isTreeItemFolder,
  ROOT_FOLDER_PATH,
  type TreeItemData,
} from "../../-utils";

interface Props {
  path: string;
  item: TreeItemData;
  disabled?: boolean;
}

function TreeItem({ item: treeData, path, disabled }: Props) {
  const params = useParams({ from: "/_authenticated/studies/$studyId/explore/user-resources/" });
  const name = isTreeItemFolder(treeData) ? treeData.name : treeData;
  const Icon = path === ROOT_FOLDER_PATH ? null : getTreeItemIcon(getTreeItemType(treeData));

  return (
    <RouterTreeItem
      to="/studies/$studyId/explore/user-resources"
      params={params}
      search={{ path }}
      itemId={path}
      label={
        <Tooltip title={name}>
          <Box sx={{ display: "flex" }}>
            {Icon && <Icon sx={{ width: 20, height: "auto", p: 0.2, mr: 0.5 }} />}
            <Box
              sx={{
                textOverflow: "ellipsis",
                overflow: "hidden",
                whiteSpace: "nowrap",
              }}
            >
              {name}
            </Box>
          </Box>
        </Tooltip>
      }
      disabled={disabled}
      slots={path === ROOT_FOLDER_PATH ? { iconContainer: HomeIcon } : undefined}
    >
      {isTreeItemFolder(treeData) &&
        [...treeData.directories, ...treeData.files].map((data) => {
          const itemName = isTreeItemFolder(data) ? data.name : data;

          return (
            <TreeItem
              key={itemName}
              path={path ? `${path}/${itemName}` : itemName}
              item={data}
              disabled={disabled}
            />
          );
        })}
    </RouterTreeItem>
  );
}

export default TreeItem;
