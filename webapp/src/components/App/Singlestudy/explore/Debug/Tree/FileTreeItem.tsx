import { Box } from "@mui/material";
import { TreeItem } from "@mui/x-tree-view/TreeItem";
import { TreeData, getFileType, getFileIcon, isFolder } from "../utils";
import DebugContext from "../DebugContext";
import { useContext } from "react";

interface Props {
  name: string;
  path: string;
  treeData: TreeData;
}

function FileTreeItem({ name, treeData, path }: Props) {
  const { setSelectedFile } = useContext(DebugContext);
  const filePath = path ? `${path}/${name}` : name;
  const fileType = getFileType(treeData);
  const FileIcon = getFileIcon(fileType);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = () => {
    setSelectedFile({ fileType, filename: name, filePath, treeData });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TreeItem
      itemId={filePath}
      label={
        <Box sx={{ display: "flex" }}>
          <FileIcon sx={{ width: 20, height: "auto", p: 0.2, mr: 0.5 }} />
          {name}
        </Box>
      }
      onClick={handleClick}
    >
      {isFolder(treeData) &&
        Object.keys(treeData).map((childName) => (
          <FileTreeItem
            key={childName}
            name={childName}
            path={filePath}
            treeData={treeData[childName]}
          />
        ))}
    </TreeItem>
  );
}

export default FileTreeItem;
