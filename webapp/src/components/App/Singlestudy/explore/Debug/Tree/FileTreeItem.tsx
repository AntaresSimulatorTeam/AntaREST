import { Box } from "@mui/material";
import { TreeItem, type TreeItemProps } from "@mui/x-tree-view/TreeItem";
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
  const canExpand = isFolder(treeData) && Object.keys(treeData).length > 0;

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleClick: TreeItemProps["onClick"] = ({ target }) => {
    // The item is not selected if the click is on the expand/collapse icon
    if (
      canExpand &&
      target instanceof Element &&
      target.closest(".MuiTreeItem-iconContainer")
    ) {
      return;
    }

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
      sx={{
        ".MuiTreeItem-content": {
          p: 0,
          alignItems: "normal",
          // Expand/collapse icon
          ".MuiTreeItem-iconContainer": {
            alignItems: "center",
            borderTopLeftRadius: "inherit",
            borderBottomLeftRadius: "inherit",
            "&:hover": {
              background: canExpand ? "inherit" : "none",
            },
          },
          ".MuiTreeItem-label": {
            py: 0.5,
          },
        },
      }}
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
