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
import { Box, Tooltip } from "@mui/material";
import { useParams } from "@tanstack/react-router";
import { getFileIcon, getFileType, isFolder, type TreeData } from "../../-utils";

interface Props {
  name: string;
  path: string;
  treeData: TreeData;
  disabled?: boolean;
}

function FileTreeItem({ name, treeData, path, disabled }: Props) {
  const params = useParams({ from: "/_authenticated/studies/$studyId/explore/debug/" });
  const filePath = path ? `${path}/${name}` : name;
  const fileType = getFileType(treeData);
  const FileIcon = getFileIcon(fileType);

  return (
    <RouterTreeItem
      to="/studies/$studyId/explore/debug"
      params={params}
      search={{ path: filePath }}
      itemId={filePath}
      label={
        <Tooltip title={name}>
          <Box sx={{ display: "flex" }}>
            <FileIcon sx={{ width: 20, height: "auto", p: 0.2, mr: 0.5 }} />
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
    >
      {isFolder(treeData) &&
        Object.keys(treeData).map((childName) => (
          <FileTreeItem
            key={childName}
            name={childName}
            path={filePath}
            treeData={treeData[childName]}
            disabled={disabled}
          />
        ))}
    </RouterTreeItem>
  );
}

export default FileTreeItem;
