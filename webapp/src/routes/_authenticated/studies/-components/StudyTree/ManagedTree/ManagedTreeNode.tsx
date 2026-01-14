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

import * as R from "ramda";
import { useMemo } from "react";
import TreeItemEnhanced from "@/components/TreeItemEnhanced";
import { ROOT_NODE_NAME } from "@/components/utils/constants";
import { treeItemStyles, treeNodeIcons } from "./styles";
import type { ManagedTreeNodeProps } from "./types";

function ManagedTreeNode({ node, onNodeClick, selectedPath }: ManagedTreeNodeProps) {
  const { children, path, name } = node;
  const isRootNode = name === ROOT_NODE_NAME;
  const hasChildren = children.length > 0;

  const sortedChildren = useMemo(
    () => R.sortBy(R.compose(R.toLower, R.prop("name")), children),
    [children],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (isRootNode) {
    return (
      <>
        {sortedChildren.map((child) => (
          <ManagedTreeNode
            key={child.id}
            node={child}
            onNodeClick={onNodeClick}
            selectedPath={selectedPath}
          />
        ))}
      </>
    );
  }

  return (
    <TreeItemEnhanced
      itemId={path}
      label={name}
      onClick={() => onNodeClick(path)}
      slots={{
        collapseIcon: hasChildren ? treeNodeIcons.folderOpen : undefined,
        expandIcon: hasChildren ? treeNodeIcons.folder : undefined,
      }}
      sx={treeItemStyles}
    >
      {sortedChildren.map((child) => (
        <ManagedTreeNode
          key={child.id}
          node={child}
          onNodeClick={onNodeClick}
          selectedPath={selectedPath}
        />
      ))}
    </TreeItemEnhanced>
  );
}

export default ManagedTreeNode;
