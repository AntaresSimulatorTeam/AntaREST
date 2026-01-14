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

import TreeItemEnhanced from "@/components/TreeItemEnhanced";
import { ROOT_NODE_NAME } from "@/components/utils/constants";
import * as R from "ramda";
import { useMemo } from "react";
import type { ManagedTreeNodeProps } from "./types";

export default function ManagedTreeNode({ node, onNodeClick, selectedPath }: ManagedTreeNodeProps) {
  const { children, path, name } = node;
  const isRootNode = name === ROOT_NODE_NAME;

  // Sort children by name (case-insensitive)
  const sortedChildren = useMemo(() => {
    return R.sortBy(R.compose(R.toLower, R.prop("name")), children);
  }, [children]);

  // Don't render root node itself, only its children
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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TreeItemEnhanced itemId={path} label={name} onClick={() => onNodeClick(path)}>
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
