import React from 'react';
import { Graph, GraphLink, GraphNode } from 'react-d3-graph';
import NodeView from './NodeView';
import { LinkProperties, NodeProperties } from './types';

interface GraphViewProps {
    nodeData: Array<NodeProperties>;
    linkData: Array<LinkProperties>;
    height: number;
    width: number;
    onClickNode: (nodeId: string) => void;
    onClickLink: (src: string, target: string) => void;
    graph: React.RefObject<Graph<NodeProperties & GraphNode, LinkProperties & GraphLink>>;
    setSelectedItem: (item: NodeProperties | LinkProperties | undefined) => void;
    onLink: (id: string) => void;
    onNodePositionChange: (id: string, x: number, y: number) => void;
  }

const GraphView = (props: GraphViewProps) => {
  const { nodeData, linkData, height, width, onClickNode, onClickLink, graph, setSelectedItem, onLink, onNodePositionChange } = props;
  let nodeDataToRender = nodeData;
  const initialZoom = 1;
  if (nodeData.length > 0) {
    const centerVector = { x: (width / initialZoom / 2), y: (height / 2) };

    const realCenter = {
      y: 0,
      x: 0,
    };

    nodeDataToRender = nodeData.map((area) => ({
      ...area,
      x: (area.x + centerVector.x - realCenter.x),
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
          viewGenerator: (node) => <NodeView node={node} linkCreation={onLink} />,
        },
        link: {
          color: '#d3d3d3',
          strokeWidth: 2,
        },
      }}
      onClickNode={onClickNode}
      onClickLink={onClickLink}
      onClickGraph={() => setSelectedItem(undefined)}
      // eslint-disable-next-line @typescript-eslint/camelcase
      onNodePositionChange={(id, x, y) => onNodePositionChange(id, x - (width / initialZoom / 2) - 0, -y + (height / 2) + 0)}
    />

  );
};

export default GraphView;
