import React from 'react';
import { Graph, GraphLink, GraphNode } from 'react-d3-graph';
import NodeView from './NodeView';
import { ColorProperties, LinkProperties, NodeProperties } from './types';

interface GraphViewProps {
    nodeData: Array<NodeProperties>;
    linkData: Array<LinkProperties>;
    height: number;
    width: number;
    onClickNode: (nodeId: string) => void;
    onClickLink: (src: string, target: string) => void;
    graph: React.RefObject<Graph<NodeProperties & GraphNode, LinkProperties & GraphLink>>;
    colors: Array<ColorProperties>;
  }

const GraphView = (props: GraphViewProps) => {
  const { nodeData, linkData, height, width, onClickNode, onClickLink, graph, colors } = props;
  let nodeDataToRender = nodeData;
  const initialZoom = 1;
  if (nodeData.length > 0) {
    // compute original enclosing rectange
    /* const enclosingRect = nodeData.reduce((acc, currentNode) => ({
      xmax: acc.xmax > currentNode.x ? acc.xmax : currentNode.x,
      xmin: acc.xmin < currentNode.x ? acc.xmin : currentNode.x,
      ymax: acc.ymax > currentNode.y ? acc.ymax : currentNode.y,
      ymin: acc.ymin < currentNode.y ? acc.ymin : currentNode.y,
    }), { xmax: nodeData[0].x, xmin: nodeData[0].x, ymax: nodeData[0].y, ymin: nodeData[0].y }); */

    // get min scale (don't scale up)

    // compute center offset with scale fix on x axis
    const centerVector = { x: (width / initialZoom / 2), y: (height / 2) };

    // get real center from origin enclosing rectangle
    const realCenter = {
      y: 0,
      x: 0,
    };
    // apply translations (y axis is inverted)
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
          viewGenerator: (node) => <NodeView node={node} color={colors.find((el) => el.id === node.id) || { id: 'none', r: 0, g: 0, b: 0 }} />,
        },
        link: {
          color: '#d3d3d3',
          strokeWidth: 2,
        },
      }}
      onClickNode={onClickNode}
      onClickLink={onClickLink}
    />

  );
};

export default GraphView;
