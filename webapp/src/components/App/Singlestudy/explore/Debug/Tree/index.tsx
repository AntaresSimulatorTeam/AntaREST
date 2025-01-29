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

import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import FileTreeItem from "./FileTreeItem";
import type { TreeFolder } from "../utils";
import { getParentPaths } from "../../../../../../utils/pathUtils";

interface Props {
  data: TreeFolder;
  // `currentPath` must not be `undefined` to make `SimpleTreeView` controlled
  currentPath: string | null;
  expandedItems: string[];
  setExpandedItems: React.Dispatch<React.SetStateAction<string[]>>;
}

function Tree(props: Props) {
  const { data, currentPath, expandedItems, setExpandedItems } = props;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleExpandedItemsChange = (event: React.SyntheticEvent, itemIds: string[]) => {
    setExpandedItems(itemIds);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // `SimpleTreeView` must be controlled because selected item can be changed manually
  // by `Folder` component, or by the `path` URL parameter at view mount.
  // The use of `selectedItems` and `expandedItems` make the component controlled.

  return (
    <SimpleTreeView
      multiSelect={false}
      selectedItems={currentPath}
      expandedItems={
        currentPath
          ? // `getParentPaths` is needed when the selected item is changed by code
            [...expandedItems, ...getParentPaths(currentPath)]
          : expandedItems
      }
      onExpandedItemsChange={handleExpandedItemsChange}
    >
      {Object.keys(data).map((filename) => (
        <FileTreeItem key={filename} name={filename} treeData={data[filename]} path="" />
      ))}
    </SimpleTreeView>
  );
}

export default Tree;
