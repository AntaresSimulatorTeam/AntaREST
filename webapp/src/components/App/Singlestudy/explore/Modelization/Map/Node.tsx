import AddLinkIcon from "@mui/icons-material/AddLink";
import { StudyMapNode } from "../../../../../../redux/ducks/studyMaps";
import { NodeContainer, NodeDefault, NodeHighlighted } from "./style";

interface PropType {
  node: StudyMapNode;
  linkCreation: (id: string) => void;
}

function Node(props: PropType) {
  const { node, linkCreation } = props;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <NodeContainer>
      {node.highlighted ? (
        <NodeHighlighted
          size="small"
          label={node.name}
          clickable
          nodecolor={node.color}
          rgbcolor={node.rgbColor}
        />
      ) : (
        <NodeDefault
          size="small"
          label={node.name}
          clickable
          nodecolor={node.color}
          rgbcolor={node.rgbColor}
          onDelete={() => linkCreation(node.id)}
          deleteIcon={<AddLinkIcon />}
        />
      )}
    </NodeContainer>
  );
}

export default Node;
