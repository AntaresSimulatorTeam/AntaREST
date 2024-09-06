import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import FileTreeItem from "./FileTreeItem";
import type { TreeFolder } from "../utils";
import { useState } from "react";

interface Props {
  data: TreeFolder;
  // `selectedItems` must not be undefined to make `SimpleTreeView` controlled
  selectedItemId: string | null;
}

function getParentItemIds(itemId: string) {
  // "a/b/c/d" -> ["a", "a/b", "a/b/c"]
  return itemId
    .split("/")
    .slice(0, -1) // Remove the last item
    .map((_, index, arr) => arr.slice(0, index + 1).join("/"));
}

function Tree({ data, selectedItemId }: Props) {
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleExpandedItemsChange = (
    event: React.SyntheticEvent,
    itemIds: string[],
  ) => {
    setExpandedItems(itemIds);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // `SimpleTreeView` must be controlled because selected item can be changed manually
  // by `Folder` component

  return (
    <SimpleTreeView
      selectedItems={selectedItemId}
      expandedItems={
        selectedItemId
          ? [...expandedItems, ...getParentItemIds(selectedItemId)]
          : expandedItems
      }
      onExpandedItemsChange={handleExpandedItemsChange}
    >
      {Object.keys(data).map((filename) => (
        <FileTreeItem
          key={filename}
          name={filename}
          treeData={data[filename]}
          path=""
        />
      ))}
    </SimpleTreeView>
  );
}

export default Tree;
