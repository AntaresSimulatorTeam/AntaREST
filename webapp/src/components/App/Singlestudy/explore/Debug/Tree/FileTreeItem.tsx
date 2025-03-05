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

import { Box, Tooltip } from "@mui/material";
import { getFileType, getFileIcon, isFolder, type TreeData } from "../utils";
import DebugContext from "../DebugContext";
import { useContext } from "react";
import TreeItemEnhanced from "../../../../../common/TreeItemEnhanced";

interface Props {
  name: string;
  path: string;
  treeData: TreeData;
}

function FileTreeItem({ name, treeData, path }: Props) {
  const { setSelectedFile } = useContext(DebugContext);
  const filePath = path ? `${path}/${name}` : name;
  const fileType = getFileType(treeData);
  const FileIcon = getFileIcon(fileType);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = () => {
    setSelectedFile({ fileType, filename: name, filePath, treeData });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TreeItemEnhanced
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
      onClick={handleClick}
    >
      {isFolder(treeData) &&
        Object.keys(treeData).map((childName) => (
          <FileTreeItem
            key={childName}
            name={childName}
            path={filePath}
            treeData={treeData[childName]}
          />
        ))}
    </TreeItemEnhanced>
  );
}

export default FileTreeItem;
