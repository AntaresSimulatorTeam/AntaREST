import { RefObject } from "react";
import { Graph, GraphLink, GraphNode } from "react-d3-graph";
import { LinkProperties, NodeProperties } from "../../../../../../common/types";
import NodeView from "./NodeView";

interface GraphViewProps {
  nodeData: Array<NodeProperties>;
  linkData: Array<LinkProperties>;
  height: number;
  width: number;
  onClickNode: (nodeId: string) => void;
  onClickLink: (src: string, target: string) => void;
  graph: RefObject<
    Graph<NodeProperties & GraphNode, LinkProperties & GraphLink>
  >;
  setSelectedItem: (item: NodeProperties | LinkProperties | undefined) => void;
  onLink: (id: string) => void;
  onNodePositionChange: (id: string, x: number, y: number) => void;
}

function GraphView(props: GraphViewProps) {
  const {
    nodeData,
    linkData,
    height,
    width,
    onClickNode,
    onClickLink,
    graph,
    setSelectedItem,
    onLink,
    onNodePositionChange,
  } = props;
  let nodeDataToRender = nodeData;
  const initialZoom = 1;
  if (nodeData.length > 0) {
    // compute center offset with scale fix on x axis
    const centerVector = { x: width / initialZoom / 2, y: height / 2 };

    // get real center from origin enclosing rectangle
    const realCenter = {
      y: 0,
      x: 0,
    };
    // apply translations (y axis is inverted)
    nodeDataToRender = nodeData.map((area) => ({
      ...area,
      x: area.x + centerVector.x - realCenter.x,
      y: -area.y + centerVector.y + realCenter.y,
    }));
  }
  return (
    <Graph
      id="graph-id"
      ref={graph}
      data={{
        nodes: nodeDataToRender,
        links: linkData,
      }}
      config={{
        height,
        width,
        highlightDegree: 0,
        staticGraphWithDragAndDrop: true,
        d3: {
          disableLinkForce: true,
        },
        node: {
          renderLabel: false,
          // eslint-disable-next-line react/no-unstable-nested-components
          viewGenerator: (node) => (
            <NodeView node={node} linkCreation={onLink} />
          ),
        },
        link: {
          color: "#a3a3a3",
          strokeWidth: 2,
        },
      }}
      onClickNode={onClickNode}
      onClickLink={onClickLink}
      onClickGraph={() => setSelectedItem(undefined)}
      onNodePositionChange={(id, x, y) =>
        onNodePositionChange(
          id,
          x - width / initialZoom / 2 - 0,
          -y + height / 2 + 0
        )
      }
    />
  );
}

export default GraphView;
