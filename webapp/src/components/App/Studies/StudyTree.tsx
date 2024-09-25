import { StudyTreeNode } from "./utils";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudiesTree, getStudyFilters } from "../../../redux/selectors";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { updateStudyFilters } from "../../../redux/ducks/studies";
import TreeItemEnhanced from "../../common/TreeItemEnhanced";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { getParentPaths } from "../../../utils/pathUtils";
import * as R from "ramda";

function StudyTree() {
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);
  const studiesTree = useAppSelector(getStudiesTree);
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTreeItemClick = (itemId: string) => {
    dispatch(updateStudyFilters({ folder: itemId }));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const buildTree = (children: StudyTreeNode[], parentId?: string) => {
    return children.map((elm) => {
      const id = parentId ? `${parentId}/${elm.name}` : elm.name;

      return (
        <TreeItemEnhanced
          key={id}
          itemId={id}
          label={elm.name}
          onClick={() => handleTreeItemClick(id)}
        >
          {buildTree(elm.children, id)}
        </TreeItemEnhanced>
      );
    });
  };

  return (
    <SimpleTreeView
      defaultExpandedItems={[...getParentPaths(folder), folder]}
      defaultSelectedItems={folder}
      sx={{ flexGrow: 1, height: 0, width: 1, py: 1 }}
    >
      {buildTree([studiesTree])}
    </SimpleTreeView>
  );
}

export default StudyTree;
