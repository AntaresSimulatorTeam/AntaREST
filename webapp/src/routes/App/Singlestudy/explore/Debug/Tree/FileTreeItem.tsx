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
import { useContext } from "react";
import TreeItemEnhanced from "../../../../../common/TreeItemEnhanced";
import DebugContext from "../DebugContext";
import { getFileIcon, getFileType, isFolder, type TreeData } from "../utils";

interface Props {
  name: string;
  path: string;
  treeData: TreeData;
  disabled?: boolean;
}

function FileTreeItem({ name, treeData, path, disabled }: Props) {
  const { setSelectedFile } = useContext(DebugContext);
  const filePath = path ? `${path}/${name}` : name;
  const fileType = getFileType(treeData);
  const FileIcon = getFileIcon(fileType);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = () => {
    if (!disabled) {
      setSelectedFile({ fileType, filename: name, filePath, treeData });
    }
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
    </TreeItemEnhanced>
  );
}

export default FileTreeItem;
