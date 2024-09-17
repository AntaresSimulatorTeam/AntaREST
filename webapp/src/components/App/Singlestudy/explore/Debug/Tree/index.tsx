import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import ArrowRightIcon from "@mui/icons-material/ArrowRight";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import FileTreeItem from "./FileTreeItem";
import { getParentPaths, type TreeFolder } from "../utils";

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
  // by `Folder` component, or by the `path` URL parameter at view mount.
  // The use of `selectedItems` and `expandedItems` make the component controlled.

  return (
    <SimpleTreeView
      selectedItems={currentPath}
      expandedItems={
        currentPath
          ? // `getParentPaths` is needed when the selected item is changed by code
            [...expandedItems, ...getParentPaths(currentPath)]
          : expandedItems
      }
      onExpandedItemsChange={handleExpandedItemsChange}
      slots={{
        expandIcon: ArrowRightIcon,
        collapseIcon: ArrowDropDownIcon,
      }}
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
