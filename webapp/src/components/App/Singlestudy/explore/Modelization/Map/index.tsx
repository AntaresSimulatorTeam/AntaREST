import { useEffect, useMemo, useRef, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Fab } from "@mui/material";
import AutoSizer from "react-virtualized-auto-sizer";
import { useTranslation } from "react-i18next";
import { Graph, GraphLink, GraphNode } from "react-d3-graph";
import { AxiosError } from "axios";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import SettingsIcon from "@mui/icons-material/Settings";
import {
  LinkProperties,
  StudyMetadata,
  UpdateAreaUi,
} from "../../../../../../common/types";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import MapGraph from "./MapGraph";
import Areas from "./Areas";
import CreateAreaDialog from "./CreateAreaDialog";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import { getUpdatedNode, NODE_COLOR } from "./utils";
import { MapContainer, MapFooter } from "./style";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import {
  getCurrentLayer,
  getCurrentStudyMapNode,
  getStudyMapLinks,
  getStudyMapNodes,
} from "../../../../../../redux/selectors";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import MapConfig from "./MapConfig";
import useStudyMaps from "../../../../../../redux/hooks/useStudyMaps";
import {
  StudyMapNode,
  createStudyMapNode,
  updateStudyMapNode,
} from "../../../../../../redux/ducks/studyMaps";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import MapHeader from "./MapHeader";

function Map() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [openDialog, setOpenDialog] = useState(false);
  const [openConfig, setOpenConfig] = useState(false);
  const previousNode = useRef<string>();
  const graphRef =
    useRef<Graph<GraphNode & StudyMapNode, GraphLink & LinkProperties>>(null);
  const currentLayerId = useAppSelector(getCurrentLayer);
  const currentArea = useAppSelector(getCurrentStudyMapNode);
  const studyLinks = useAppSelector((state) =>
    getStudyMapLinks(state, study.id)
  );
  const mapLinks = useMemo(
    () =>
      R.map(
        RA.renameKeys({ area1: "source", area2: "target" }),
        studyLinks || []
      ) as LinkProperties[],
    [studyLinks]
  );
  const mapNodesRes = useStudyMaps({
    studyId: study.id,
    selector: getStudyMapNodes,
  });

  /**
   * Sets highlight mode on node click
   */
  useEffect(() => {
    const { current } = graphRef;
    if (current) {
      if (previousNode.current) {
        // eslint-disable-next-line no-underscore-dangle
        current._setNodeHighlightedValue(previousNode.current, false);
      }

      if (currentArea) {
        const timerId = setTimeout(() => {
          // eslint-disable-next-line no-underscore-dangle
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

  const updateUI = async (nodeId: string, nodeUI: UpdateAreaUi) => {
    const updatedNode = getUpdatedNode(nodeId, mapNodesRes.data || []);
    /**
     * Compare the new node position: @nodeUI and the existing one: @updatedNode
     * If they are not equal the UI should be updated
     */
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

  const handleCreateArea = async (name: string) => {
    setOpenDialog(false);
    try {
      if (study) {
        dispatch(createStudyMapNode({ studyId: study.id, name }));
      }
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.createArea"), e as AxiosError);
    }
  };

  const handlePositionChange = async (id: string, x: number, y: number) => {
    const updatedNode = getUpdatedNode(id, mapNodesRes.data || []);
    if (updatedNode) {
      const { layerX, layerY, layerColor } = updatedNode;
      updateUI(id, {
        x,
        y,
        color_rgb: layerColor[currentLayerId]
          ? layerColor[currentLayerId].split(",").map(Number)
          : NODE_COLOR.slice(4, -1).split(",").map(Number),
        layerX,
        layerY,
        layerColor,
      });
    }
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
      ifResolved={(mapNodes) => (
        <>
          <SplitLayoutView
            left={
              <Areas
                onAdd={() => setOpenDialog(true)}
                nodes={mapNodes}
                updateUI={updateUI}
              />
            }
            right={
              openConfig ? (
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
                      />
                    )}
                  </AutoSizer>
                  <MapFooter>
                    <Fab
                      size="small"
                      color="default"
                      onClick={() => {
                        setOpenConfig(true);
                      }}
                    >
                      <SettingsIcon />
                    </Fab>
                  </MapFooter>
                </MapContainer>
              )
            }
          />
          {openDialog && (
            <CreateAreaDialog
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

export default Map;
