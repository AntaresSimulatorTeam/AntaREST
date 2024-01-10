import { TreeView } from "@mui/x-tree-view";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import FileTreeItem from "./FileTreeItem";
import { useDebugContext } from "../DebugContext";

function Tree() {
  const { treeData } = useDebugContext();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TreeView
      multiSelect
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<ChevronRightIcon />}
    >
      {typeof treeData === "object" &&
        Object.keys(treeData).map((key) => (
          <FileTreeItem key={key} name={key} content={treeData[key]} path="" />
        ))}
    </TreeView>
  );
}

export default Tree;
