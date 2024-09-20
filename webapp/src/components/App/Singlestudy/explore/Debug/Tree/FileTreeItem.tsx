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

import { Box } from "@mui/material";
import { TreeItem } from "@mui/x-tree-view";
import { TreeData, determineFileType, getFileIcon } from "../utils";
import { useDebugContext } from "../DebugContext";

interface Props {
  name: string;
  content: TreeData;
  path: string;
}

function FileTreeItem({ name, content, path }: Props) {
  const { onFileSelect } = useDebugContext();
  const filePath = `${path}/${name}`;
  const fileType = determineFileType(content);
  const FileIcon = getFileIcon(fileType);
  const isFolderEmpty = !Object.keys(content).length;

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = () => {
    if (fileType !== "folder") {
      onFileSelect({ fileType, filePath });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TreeItem
      nodeId={filePath}
      label={
        <Box
          role="button"
          sx={{
            display: "flex",
            alignItems: "center",
            ...(isFolderEmpty && { opacity: 0.5 }),
          }}
          onClick={handleClick}
        >
          <FileIcon sx={{ width: 20, height: "auto", p: 0.2 }} />
          <span style={{ marginLeft: 4 }}>{name}</span>
        </Box>
      }
    >
      {typeof content === "object" &&
        Object.keys(content).map((childName) => (
          <FileTreeItem
            key={childName}
            name={childName}
            content={content[childName]}
            path={filePath}
          />
        ))}
    </TreeItem>
  );
}

export default FileTreeItem;
