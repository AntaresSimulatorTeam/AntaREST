import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import FileTreeItem from "./FileTreeItem";
import type { TreeFolder } from "../utils";

interface Props {
  data: TreeFolder;
}

function Tree({ data }: Props) {
  return (
    <SimpleTreeView>
      {Object.keys(data).map((key) => (
        <FileTreeItem key={key} name={key} content={data[key]} path="" />
      ))}
    </SimpleTreeView>
  );
}

export default Tree;
