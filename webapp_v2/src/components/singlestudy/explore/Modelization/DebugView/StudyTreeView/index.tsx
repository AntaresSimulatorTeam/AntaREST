/* eslint-disable jsx-a11y/interactive-supports-focus */
/* eslint-disable jsx-a11y/click-events-have-key-events */
import { Box } from "@mui/material";
import { TreeItem, TreeView } from "@mui/lab";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { StudyDataType } from "../../../../../../common/types";
import { getStudyParams } from "./utils";

interface ItemPropTypes {
  itemkey: string;
  data: any;
  path?: string;
  viewer: (type: StudyDataType, data: string) => void;
}

function StudyTreeItem(props: ItemPropTypes) {
  const { itemkey, data, path = "/", viewer } = props;

  // if not an object then it's a RawFileNode or MatrixNode
  // here we have to decide which viewer to use
  const params = getStudyParams(data, path, itemkey);
  if (params) {
    const FileIcon = params.icon;
    return (
      <TreeItem
        nodeId={`${path}/${itemkey}`}
        label={
          <Box
            role="button"
            display="flex"
            alignItems="center"
            onClick={() => viewer(params.type, params.data)}
          >
            <FileIcon
              sx={{
                width: "22px",
                height: "auto",
                p: 0.2,
              }}
            />
            <span style={{ marginLeft: "4px" }}>{itemkey}</span>
          </Box>
        }
      />
    );
  }

  // else this is a folder containing.. stuff (recursion)
  return (
    <TreeItem nodeId={`${path}/${itemkey}`} label={itemkey}>
      {Object.keys(data).map((childkey) => (
        <StudyTreeItem
          key={childkey}
          itemkey={childkey}
          data={data[childkey]}
          path={`${path}/${itemkey}`}
          viewer={viewer}
        />
      ))}
    </TreeItem>
  );
}

interface PropTypes {
  data: any;
  view: (type: StudyDataType, data: string) => void;
}

function StudyTreeView(props: PropTypes) {
  const { data, view } = props;
  return (
    <TreeView
      multiSelect
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<ChevronRightIcon />}
    >
      {Object.keys(data).map((key) => (
        <StudyTreeItem key={key} itemkey={key} data={data[key]} viewer={view} />
      ))}
    </TreeView>
  );
}

StudyTreeItem.defaultProps = {
  path: "/",
};

export default StudyTreeView;
