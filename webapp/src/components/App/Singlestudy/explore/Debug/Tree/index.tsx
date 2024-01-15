import { TreeView } from "@mui/x-tree-view";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import FileTreeItem from "./FileTreeItem";
import { TreeData } from "../utils";

interface Props {
  data: TreeData;
}

function Tree({ data }: Props) {
  return (
    <TreeView
      multiSelect
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<ChevronRightIcon />}
    >
      {typeof data === "object" &&
        Object.keys(data).map((key) => (
          <FileTreeItem key={key} name={key} content={data[key]} path="" />
        ))}
    </TreeView>
  );
}

export default Tree;
