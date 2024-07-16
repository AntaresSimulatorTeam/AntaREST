import { Box } from "@mui/material";
import { TreeItem } from "@mui/x-tree-view/TreeItem";
import { TreeData, getFileType, getFileIcon, isFolder } from "../utils";
import DebugContext from "../DebugContext";
import { useContext } from "react";

interface Props {
  name: string;
  content: TreeData;
  path: string;
}

function FileTreeItem({ name, content, path }: Props) {
  const { onFileSelect } = useContext(DebugContext);
  const filePath = `${path}/${name}`;
  const fileType = getFileType(content);
  const FileIcon = getFileIcon(fileType);

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
      itemId={filePath}
      label={
        <Box sx={{ display: "flex" }}>
          <FileIcon sx={{ width: 20, height: "auto", p: 0.2, mr: 0.5 }} />
          {name}
        </Box>
      }
      onClick={handleClick}
    >
      {isFolder(content) &&
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
