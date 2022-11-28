import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Fab, Typography } from "@mui/material";
import AutoSizer from "react-virtualized-auto-sizer";
import { useTranslation } from "react-i18next";
import { Graph, GraphLink, GraphNode } from "react-d3-graph";
import { AxiosError } from "axios";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import SettingsIcon from "@mui/icons-material/Settings";
import {
  LinkProperties,
  NodeProperties,
  StudyMetadata,
  UpdateAreaUi,
} from "../../../../../../common/types";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import MapGraph from "./MapGraph";
import Areas from "./Areas";
import CreateAreaDialog from "./CreateAreaDialog";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import {
  getUpdatedNode,
  useSetCurrentNode,
  useSetSelectedNodeLinks,
} from "./utils";
import { MapContainer, MapHeader } from "./style";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getLinks } from "../../../../../../redux/selectors";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import {
  createMapNode,
  fetchNodesData,
  updateMapNodeUI,
} from "../../../../../../redux/ducks/studyDataSynthesis";
import MapConfig from "./MapConfig";

function Map() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [openDialog, setOpenDialog] = useState<boolean>(false);
  const [isLoaded, setIsLoaded] = useState<boolean>(false);
  const [openConfig, setOpenConfig] = useState<boolean>(false);
  const previousNode = useRef<string>();
  const graphRef =
    useRef<Graph<GraphNode & NodeProperties, GraphLink & LinkProperties>>(null);

  ////////////////////////////////////////////////////////////////
  // Selectors
  ////////////////////////////////////////////////////////////////

  const selectedNode = useAppSelector(getSelectedNode);
  const mapNodes = useAppSelector(getMapNodes);
  const studyLinks = useAppSelector((state) => getLinks(state, study.id));
  const mapLinks = useMemo(
    () =>
      R.map(
        RA.renameKeys({ area1: "source", area2: "target" }),
        studyLinks
      ) as LinkProperties[],
    [studyLinks]
  );

  useSetCurrentNode(selectedNode);
  useSetSelectedNodeLinks(selectedNode, mapLinks);
  useStudySynthesis({
    studyId: study.id,
    selector: (state) => ({
      areas: state.areas,
    }),
  });

  useEffect(() => {
    const fetchNodes = async (): Promise<void> => {
      try {
        setIsLoaded(false);
        await dispatch(fetchNodesData(study.id));
      } catch (e) {
        enqueueErrorSnackbar(t("study.error.getAreasInfo"), e as AxiosError);
      } finally {
        setIsLoaded(true);
      }
    };

    fetchNodes();
  }, [dispatch, enqueueErrorSnackbar, study.id, t]);

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

      if (selectedNode) {
        const timerId = setTimeout(() => {
          // eslint-disable-next-line no-underscore-dangle
          current._setNodeHighlightedValue(selectedNode.id, true);
          previousNode.current = selectedNode.id;
        }, 20);

        return () => {
          clearTimeout(timerId);
        };
      }
    }
  }, [selectedNode, dispatch]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const updateUI = async (nodeId: string, nodeUI: UpdateAreaUi) => {
    const updatedNode = getUpdatedNode(nodeId, mapNodes);
    /**
     * Compare the new node position: @nodeUI and the existing one: @updatedNode
     * If they are not equal the UI should be updated
     */
    const updatedUI = !R.whereEq(nodeUI, updatedNode);

    if (updatedUI) {
      try {
        if (study) {
          await dispatch(
            updateMapNodeUI({ studyId: study.id, nodeId, nodeUI })
          );
        }
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
        await dispatch(createMapNode({ studyId: study.id, name }));
      }
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.createArea"), e as AxiosError);
    }
  };

  const handlePositionChange = async (id: string, x: number, y: number) => {
    const updatedNode = getUpdatedNode(id, mapNodes);
    if (updatedNode) {
      updateUI(id, { x, y, color_rgb: updatedNode.rgbColor });
    }
  };

  const handleClose = () => {
    setOpenDialog(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <SplitLayoutView
        left={<Areas onAdd={() => setOpenDialog(true)} updateUI={updateUI} />}
        right={
          openConfig ? (
            <MapConfig onClose={() => setOpenConfig(false)} />
          ) : (
            <MapContainer>
              <MapHeader>
                <Typography>{`${mapNodes.length} ${t(
                  "study.areas"
                )}`}</Typography>
                <Typography>
                  {`${mapLinks.length} ${t("study.links")}`}
                </Typography>
                <Fab
                  size="small"
                  color="default"
                  onClick={() => setOpenConfig(true)}
                >
                  <SettingsIcon />
                </Fab>
              </MapHeader>
              {isLoaded && !openConfig && (
                <Suspense fallback={<SimpleLoader />}>
                  <AutoSizer>
                    {({ height, width }) => (
                      <MapGraph
                        height={height}
                        width={width}
                        links={mapLinks}
                        graph={graphRef}
                        onNodePositionChange={handlePositionChange}
                      />
                    )}
                  </AutoSizer>
                </Suspense>
              )}
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
  );
}

export default Map;
