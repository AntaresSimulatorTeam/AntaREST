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

import SplitView from "@/components/page/SplitView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import { Box } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import type { AxiosError } from "axios";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Graph, GraphLink, GraphNode } from "react-d3-graph";
import { useTranslation } from "react-i18next";
import AutoSizer from "react-virtualized-auto-sizer";
import useStudy from "../../../../../../-shared/hook/useStudy";
import useDebouncedState from "../../../../../../../hooks/useDebouncedState";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import {
  createStudyMapNode,
  updateStudyMapNode,
  type StudyMapNode,
} from "../../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import useStudyMaps from "../../../../../../../redux/hooks/useStudyMaps";
import {
  getCurrentLayer,
  getCurrentStudyMapNode,
  getStudyMapLinks,
  getStudyMapNodes,
} from "../../../../../../../redux/selectors";
import type { LinkProperties, UpdateAreaUi } from "../../../../../../../types/types";
import Areas from "./-components/Areas";
import CreateAreaDialog from "./-components/CreateAreaDialog";
import MapConfig from "./-components/MapConfig";
import MapControlButtons from "./-components/MapControlButtons";
import MapGraph from "./-components/MapGraph";
import MapHeader from "./-components/MapHeader";
import { MapContainer } from "./-components/style";
import { getUpdatedNode, INITIAL_ZOOM, NODE_COLOR } from "./-utils";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/modeling/map/")({
  component: Map,
});

function Map() {
  const study = useStudy();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [openDialog, setOpenDialog] = useState(false);
  const [openConfig, setOpenConfig] = useState(false);
  const [zoomLevel, setZoomLevel] = useDebouncedState(INITIAL_ZOOM, 250);
  const previousNode = useRef<string>();
  const graphRef = useRef<Graph<GraphNode & StudyMapNode, GraphLink & LinkProperties>>(null);
  const currentLayerId = useAppSelector(getCurrentLayer);
  const currentArea = useAppSelector(getCurrentStudyMapNode);
  const studyLinks = useAppSelector((state) => getStudyMapLinks(state, study.id));
  const mapLinks = useMemo(
    () =>
      R.map(
        RA.renameKeys({ area1: "source", area2: "target" }),
        studyLinks || [],
      ) as unknown as LinkProperties[],
    [studyLinks],
  );
  const mapNodesRes = useStudyMaps({
    studyId: study.id,
    selector: getStudyMapNodes,
  });

  // Sets highlight mode on node click
  useEffect(() => {
    const { current } = graphRef;
    if (current) {
      if (previousNode.current) {
        current._setNodeHighlightedValue(previousNode.current, false);
      }

      if (currentArea) {
        const timerId = setTimeout(() => {
          current._setNodeHighlightedValue(currentArea.id, true);
          previousNode.current = currentArea.id;
        }, 20);

        return () => {
          clearTimeout(timerId);
        };
      }
    }
  }, [dispatch, currentArea]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const updateUI = (nodeId: string, nodeUI: UpdateAreaUi) => {
    const updatedNode = getUpdatedNode(nodeId, mapNodesRes.data || []);

    // Compare the new node position and the existing one, if they are not equal the UI should be updated
    const updatedUI = !R.whereEq(nodeUI, updatedNode);

    if (updatedUI && study) {
      try {
        dispatch(updateStudyMapNode({ studyId: study.id, nodeId, nodeUI }));
      } catch (e) {
        enqueueErrorSnackbar(t("study.error.updateUI"), e as AxiosError);
      }
    }
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCreateArea = (name: string) => {
    try {
      if (study) {
        return dispatch(createStudyMapNode({ studyId: study.id, name }))
          .unwrap()
          .then(() => {
            setOpenDialog(false);
          });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.createArea"), e as AxiosError);
    }
  };

  const handlePositionChange = (id: string, x: number, y: number) => {
    const updatedNode = getUpdatedNode(id, mapNodesRes.data || []);
    if (updatedNode) {
      const { layerX, layerY, layerColor } = updatedNode;
      updateUI(id, {
        x: Math.round(x),
        y: Math.round(y),
        color_rgb: layerColor[currentLayerId]
          ? layerColor[currentLayerId].split(",").map(Number)
          : NODE_COLOR.slice(4, -1).split(",").map(Number),
        layerX,
        layerY,
        layerColor,
      });
    }
  };

  const handleZoomIn = () => {
    setZoomLevel(zoomLevel + 0.3);
    setZoomLevel.flush();
  };

  const handleZoomOut = () => {
    setZoomLevel(zoomLevel - 0.3);
    setZoomLevel.flush();
  };

  const handleClose = () => {
    setOpenDialog(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={mapNodesRes}
      ifFulfilled={(mapNodes) => (
        <>
          <SplitView splitId="map">
            <Box>
              <Areas onAdd={() => setOpenDialog(true)} nodes={mapNodes} updateUI={updateUI} />
            </Box>
            <Box>
              {openConfig ? (
                <MapConfig onClose={() => setOpenConfig(false)} />
              ) : (
                <MapContainer>
                  <MapHeader links={mapLinks} nodes={mapNodes} />
                  <AutoSizer>
                    {({ height, width }) => (
                      <MapGraph
                        height={height}
                        width={width}
                        links={mapLinks}
                        nodes={mapNodes}
                        graph={graphRef}
                        onNodePositionChange={handlePositionChange}
                        zoomLevel={zoomLevel}
                        setZoomLevel={setZoomLevel}
                      />
                    )}
                  </AutoSizer>
                  <MapControlButtons
                    onZoomIn={handleZoomIn}
                    onZoomOut={handleZoomOut}
                    onOpenConfig={() => setOpenConfig(true)}
                    zoomLevel={zoomLevel}
                  />
                </MapContainer>
              )}
            </Box>
          </SplitView>

          {openDialog && (
            <CreateAreaDialog
              studyId={study.id}
              open={openDialog}
              onClose={handleClose}
              createArea={handleCreateArea}
            />
          )}
        </>
      )}
    />
  );
}
