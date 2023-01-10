import { AxiosError } from "axios";
import { RefObject, useEffect, useState } from "react";
import { Graph, GraphLink, GraphNode } from "react-d3-graph";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { LinkProperties, StudyMetadata } from "../../../../../../common/types";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import { StudyMapNode } from "../../../../../../redux/ducks/studyMaps";
import {
  setCurrentArea,
  setCurrentLink,
} from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentLayer } from "../../../../../../redux/selectors";
import { makeLinkId } from "../../../../../../redux/utils";
import { createLink } from "../../../../../../services/api/studydata";
import Node from "./Node";
import { INITIAL_ZOOM, useRenderNodes } from "./utils";

interface Props {
  height: number;
  width: number;
  links: LinkProperties[];
  nodes: StudyMapNode[];
  graph: RefObject<Graph<StudyMapNode & GraphNode, LinkProperties & GraphLink>>;
  onNodePositionChange: (id: string, x: number, y: number) => void;
}

function MapGraph(props: Props) {
  const { height, width, links, nodes, graph, onNodePositionChange } = props;
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [sourceNode, setSourceNode] = useState<string | undefined>(undefined);
  const [targetNode, setTargetNode] = useState<string | undefined>(undefined);
  const currentLayerId = useAppSelector(getCurrentLayer);
  const mapNodes = useRenderNodes(nodes, width, height, currentLayerId);

  /**
   * Reset nodes positions on layer change to prevent previous layer positions
   */
  useEffect(() => {
    if (graph.current) {
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      graph.current.resetNodesPositions();
    }
  }, [currentLayerId, graph]);

  /**
   * Create new map link if sourceNode and targetNode are set
   */
  useEffect(() => {
    const createMapLink = async (
      sourceNode: string,
      targetNode: string
    ): Promise<void> => {
      try {
        await createLink(study.id, { area1: sourceNode, area2: targetNode });
      } catch (e) {
        enqueueErrorSnackbar(t("study.error.createLink"), e as AxiosError);
      } finally {
        setSourceNode(undefined);
        setTargetNode(undefined);
      }
    };

    if (sourceNode && targetNode) {
      createMapLink(sourceNode, targetNode);
    }
  }, [sourceNode, targetNode, study.id, dispatch, enqueueErrorSnackbar, t]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLinkCreation = (nodeId: string) => {
    if (sourceNode && sourceNode === nodeId) {
      setSourceNode("");
    } else {
      setSourceNode(nodeId);
    }
  };

  const handleOnClickNode = async (nodeId: string) => {
    if (!sourceNode && nodes) {
      dispatch(setCurrentLink(""));
      dispatch(setCurrentArea(nodeId));
    }
  };

  const handleOnClickLink = (source: string, target: string) => {
    dispatch(setCurrentArea(""));
    dispatch(setCurrentLink(makeLinkId(source, target)));
  };

  const handleGraphClick = () => {
    if (sourceNode) {
      setSourceNode("");
    }
    dispatch(setCurrentArea(""));
    dispatch(setCurrentLink(""));
  };

  const handleNodePositionChange = (id: string, x: number, y: number) => {
    return onNodePositionChange(
      id,
      x - width / INITIAL_ZOOM / 2 - 0,
      -y + height / 2 + 0
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Graph
      id="graph-id"
      ref={graph}
      data={{
        nodes: mapNodes,
        links: mapNodes.length > 0 ? links : [],
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
            <Node node={node} linkCreation={handleLinkCreation} />
          ),
        },
        link: {
          color: "#a3a3a3",
          strokeWidth: 2,
        },
      }}
      onClickNode={handleOnClickNode}
      onClickLink={handleOnClickLink}
      onClickGraph={handleGraphClick}
      onNodePositionChange={handleNodePositionChange}
    />
  );
}

export default MapGraph;
