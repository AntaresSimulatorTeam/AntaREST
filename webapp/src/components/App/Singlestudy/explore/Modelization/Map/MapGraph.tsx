/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import type { AxiosError } from "axios";
import type { DebouncedFunc } from "lodash";
import { useEffect, useState } from "react";
import { Graph, type GraphLink, type GraphNode } from "react-d3-graph";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import type { LinkProperties, StudyMetadata } from "../../../../../../types/types";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import { createStudyMapLink, type StudyMapNode } from "../../../../../../redux/ducks/studyMaps";
import { setCurrentArea, setCurrentLink } from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentLayer } from "../../../../../../redux/selectors";
import { makeLinkId } from "../../../../../../redux/utils";
import Node from "./Node";
import { INITIAL_ZOOM, useRenderNodes } from "./utils";

interface Props {
  height: number;
  width: number;
  links: LinkProperties[];
  nodes: StudyMapNode[];
  graph: React.RefObject<Graph<StudyMapNode & GraphNode, LinkProperties & GraphLink>>;
  onNodePositionChange: (id: string, x: number, y: number) => void;
  zoomLevel: number;
  setZoomLevel: DebouncedFunc<(zoom: number) => void>;
}

function MapGraph({
  height,
  width,
  links,
  nodes,
  graph,
  onNodePositionChange,
  zoomLevel,
  setZoomLevel,
}: Props) {
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
    if (sourceNode && targetNode) {
      dispatch(
        createStudyMapLink({
          studyId: study.id,
          area1: sourceNode,
          area2: targetNode,
        }),
      )
        .unwrap()
        .catch((err: AxiosError) => {
          enqueueErrorSnackbar(t("study.error.createLink"), err);
        })
        .finally(() => {
          setSourceNode(undefined);
          setTargetNode(undefined);
        });
    }
  }, [sourceNode, targetNode, study.id, dispatch, enqueueErrorSnackbar, t]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLinkCreation = (nodeId: string) => {
    if (sourceNode && sourceNode === nodeId) {
      setSourceNode(undefined);
      setTargetNode(undefined);
    } else {
      setSourceNode(nodeId);
    }
  };

  const handleOnClickNode = (nodeId: string) => {
    if (!sourceNode && nodes) {
      dispatch(setCurrentLink(""));
      dispatch(setCurrentArea(nodeId));
    } else if (sourceNode) {
      setTargetNode(nodeId);
    }
  };

  const handleOnClickLink = (source: string, target: string) => {
    const isTempLink =
      links.find((link) => link.source === source && link.target === target)?.temp || false;

    if (!isTempLink) {
      dispatch(setCurrentArea(""));
      dispatch(setCurrentLink(makeLinkId(source, target)));
    }
  };

  const handleGraphClick = () => {
    if (sourceNode) {
      setSourceNode("");
    }
    dispatch(setCurrentArea(""));
    dispatch(setCurrentLink(""));
  };

  const handleNodePositionChange = (id: string, x: number, y: number) => {
    return onNodePositionChange(id, x - width / INITIAL_ZOOM / 2 - 0, -y + height / 2 + 0);
  };

  const onZoomChange = (previousZoom: number, newZoom: number) => {
    setZoomLevel(newZoom);
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
        initialZoom: zoomLevel,
        height,
        width,
        highlightDegree: 0,
        staticGraphWithDragAndDrop: true,
        d3: {
          disableLinkForce: true,
        },
        node: {
          renderLabel: false,
          viewGenerator: (node) => <Node node={node} linkCreation={handleLinkCreation} />,
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
      onZoomChange={onZoomChange}
    />
  );
}

export default MapGraph;
