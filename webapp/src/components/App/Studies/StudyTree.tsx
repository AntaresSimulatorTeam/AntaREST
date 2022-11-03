import { useCallback, Fragment } from "react";
import { Typography } from "@mui/material";
import TreeView from "@mui/lab/TreeView";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import TreeItem from "@mui/lab/TreeItem";
import { StudyTreeNode } from "./utils";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudiesTree, getStudyFilters } from "../../../redux/selectors";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { updateStudyFilters } from "../../../redux/ducks/studies";

function StudyTree() {
  const folder = useAppSelector((state) => getStudyFilters(state).folder);
  const studiesTree = useAppSelector(getStudiesTree);
  const dispatch = useAppDispatch();

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
