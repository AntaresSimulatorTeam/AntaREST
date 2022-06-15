import {
  useCallback,
  useState,
  MouseEvent as ReactMouseEvent,
  Fragment,
} from "react";
import { Menu, MenuItem, Typography } from "@mui/material";
import TreeView from "@mui/lab/TreeView";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import TreeItem from "@mui/lab/TreeItem";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { StudyTreeNode } from "./utils";
import { scanFolder } from "../../services/api/study";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import useAppSelector from "../../redux/hooks/useAppSelector";
import { getStudiesTree, getStudyFilters } from "../../redux/selectors";
import useAppDispatch from "../../redux/hooks/useAppDispatch";
import { updateStudyFilters } from "../../redux/ducks/studies";

function StudyTree() {
  const folder = useAppSelector((state) => getStudyFilters(state).folder);
  const studiesTree = useAppSelector(getStudiesTree);
  const dispatch = useAppDispatch();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [menuId, setMenuId] = useState<string>("");
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
  } | null>(null);

  const onContextMenu = (
    event: ReactMouseEvent<HTMLSpanElement, MouseEvent>,
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
    } catch (e) {
      enqueueErrorSnackbar(t("studies.error.scanFolder"), e as AxiosError);
    } finally {
      setContextMenu(null);
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
      return (
        <Fragment key={newId}>
          <TreeItem
            key={`treeitem-${newId}`}
            nodeId={newId}
            label={
              <Typography
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  dispatch(updateStudyFilters({ folder: newId }));
                }}
                onContextMenu={(e) => onContextMenu(e, elm.path)}
              >
                {elm.name}
              </Typography>
            }
            collapseIcon={
              elm.children.length > 0 ? <ExpandMoreIcon /> : undefined
            }
            expandIcon={
              elm.children.length > 0 ? <ChevronRightIcon /> : undefined
            }
          >
            {buildTree((elm as StudyTreeNode).children, newId)}
          </TreeItem>
          <Menu
            key={`menu-${newId}`}
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
              {t("studies.scanFolder")}
            </MenuItem>
          </Menu>
        </Fragment>
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
        nodeId={studiesTree.name}
        label={
          <Typography
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              dispatch(updateStudyFilters({ folder: studiesTree.name }));
            }}
          >
            {studiesTree.name}
          </Typography>
        }
        collapseIcon={
          studiesTree.children.length > 0 ? <ExpandMoreIcon /> : undefined
        }
        expandIcon={
          studiesTree.children.length > 0 ? <ChevronRightIcon /> : undefined
        }
      >
        {buildTree(studiesTree.children, studiesTree.name)}
      </TreeItem>
    </TreeView>
  );
}

export default StudyTree;
