import { useCallback, useState, MouseEvent as ReactMouseEvent } from "react";
import { Menu, MenuItem } from "@mui/material";
import TreeView from "@mui/lab/TreeView";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import TreeItem from "@mui/lab/TreeItem";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { StudyTreeNode } from "./utils";
import { scanFolder } from "../../services/api/study";
import enqueueErrorSnackbar from "../common/ErrorSnackBar";

interface Props {
  tree: StudyTreeNode;
  folder: string;
  setFolder: (folder: string) => void;
}

function StudyTree(props: Props) {
  const { tree, folder, setFolder } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();
  const [menuId, setMenuId] = useState<string>("");
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
  } | null>(null);

  const onContextMenu = (
    event: ReactMouseEvent<HTMLLIElement, MouseEvent>,
    id: string
  ) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (event as any).preventDefault();
    setContextMenu(
      contextMenu === null
        ? {
            mouseX: event.clientX - 2,
            mouseY: event.clientY - 4,
          }
        : // repeated contextmenu when it is already open closes it with Chrome 84 on Ubuntu
          // Other native context menus might behave different.
          // With this behavior we prevent contextmenu from the backdrop to re-locale existing context menus.
          null
    );
    setMenuId(id);
  };

  const handleClose = () => {
    setContextMenu(null);
  };

  const orderFolderScan = async (folderPath: string): Promise<void> => {
    try {
      await scanFolder(folderPath);
      enqueueSnackbar(t("studymanager:scanFolderSuccess"), { variant: "info" });
    } catch (e) {
      enqueueErrorSnackbar(
        enqueueSnackbar,
        t("studymanager:scanFolderError"),
        e as AxiosError
      );
    }
  };

  const getExpandedTab = (nodeId: string): Array<string> => {
    const expandedTab: Array<string> = [];
    const tab = nodeId.split("/");
    let lastnodeId = "";
    for (let i = 0; i < tab.length; i += 1) {
      lastnodeId += i === 0 ? tab[i] : `/${tab[i]}`;
      expandedTab.push(lastnodeId);
    }
    return expandedTab;
  };

  const buildTree = (children: Array<StudyTreeNode>, parentId: string) =>
    children.map((elm) => {
      const newId = `${parentId}/${elm.name}`;
      const elements = buildTree((elm as StudyTreeNode).children, newId).filter(
        (item) => item
      );
      return (
        <>
          <TreeItem
            key={newId}
            nodeId={newId}
            label={elm.name}
            expandIcon={elements.length > 0 ? <ExpandMoreIcon /> : undefined}
            collapseIcon={
              elements.length > 0 ? <ChevronRightIcon /> : undefined
            }
            onContextMenu={(e) => onContextMenu(e, elm.path)}
            onClick={() => setFolder(newId)}
          >
            {buildTree((elm as StudyTreeNode).children, newId)}
          </TreeItem>
          <Menu
            open={contextMenu !== null && menuId === elm.path}
            onClose={handleClose}
            anchorReference="anchorPosition"
            anchorPosition={
              contextMenu !== null
                ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
                : undefined
            }
          >
            <MenuItem
              onClick={() => orderFolderScan((elm as StudyTreeNode).path)}
            >
              {t("studymanager:scanFolder")}
            </MenuItem>
          </Menu>
        </>
      );
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const getDefaultSelected = useCallback(() => [folder], []);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const getDefaultExpanded = useCallback(() => getExpandedTab(folder), []);

  return (
    <TreeView
      aria-label="Study tree"
      defaultSelected={getDefaultSelected()}
      defaultExpanded={getDefaultExpanded()}
      selected={[folder]}
      sx={{ flexGrow: 1, height: 0, width: "100%", py: 1 }}
    >
      <TreeItem
        nodeId={tree.name}
        label={tree.name}
        onClick={() => setFolder(tree.name)}
        expandIcon={tree.children.length > 0 ? <ExpandMoreIcon /> : undefined}
        collapseIcon={
          tree.children.length > 0 ? <ChevronRightIcon /> : undefined
        }
      >
        {buildTree(tree.children, tree.name)}
      </TreeItem>
    </TreeView>
  );
}

export default StudyTree;
