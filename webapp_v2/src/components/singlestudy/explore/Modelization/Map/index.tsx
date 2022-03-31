/* eslint-disable react-hooks/exhaustive-deps */
import React, { useCallback, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Box, Typography } from '@mui/material';
import AutoSizer from 'react-virtualized-auto-sizer';
import { useTranslation } from 'react-i18next';
import { Graph, GraphLink, GraphNode } from 'react-d3-graph';
import { useSnackbar } from 'notistack';
import debug from 'debug';
import { AxiosError } from 'axios';
import enqueueErrorSnackbar from '../../../../common/ErrorSnackBar';
import { AreasConfig, isNode, LinkProperties, NodeProperties, SingleAreaConfig, StudyMetadata, UpdateAreaUi } from '../../../../../common/types';
import SplitLayoutView from '../../../../common/SplitLayoutView';
import { createArea, updateAreaUI, deleteArea, deleteLink, createLink } from '../../../../../services/api/studydata';
import { getAreaPositions, getSynthesis } from '../../../../../services/api/study';
import SimpleLoader from '../../../../common/loaders/SimpleLoader';
import GraphView from './GraphView';
import MapPropsView from './MapPropsView';
import CreateAreaModal from './CreateAreaModal';

const logError = debug('antares:singlestudy:modelization:map:error');

const FONT_SIZE = 15;
const NODE_HEIGHT = 400;

const calculateSize = (text: string): number => {
  const textSize = text.length;
  if (textSize === 1) {
    return FONT_SIZE * textSize * 36;
  }
  if (textSize <= 2) {
    return FONT_SIZE * textSize * 20;
  }
  if (textSize <= 3) {
    return FONT_SIZE * textSize * 12;
  }
  if (textSize <= 5) {
    return FONT_SIZE * textSize * 10;
  }
  if (textSize <= 6) {
    return FONT_SIZE * textSize * 8.5;
  }
  if (textSize <= 10) {
    return FONT_SIZE * textSize * 7.5;
  }
  return FONT_SIZE * textSize * 6.5;
};

const GraphViewMemo = React.memo(GraphView);

function Map() {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [loaded, setLoaded] = React.useState(false);
  const [selectedItem, setSelectedItem] = React.useState<NodeProperties | LinkProperties>();
  const [selectedNodeLinks, setSelectedNodeLinks] = React.useState<Array<LinkProperties>>();
  const [nodeData, setNodeData] = React.useState<Array<NodeProperties>>([]);
  const [linkData, setLinkData] = React.useState<Array<LinkProperties>>([]);
  const [openModal, setOpenModal] = React.useState<boolean>(false);
  const [firstNode, setFirstNode] = React.useState<string>();
  const [secondNode, setSecondNode] = React.useState<string>();
  const graphRef = React.useRef<Graph<GraphNode & NodeProperties, GraphLink & LinkProperties>>(null);
  const prevselectedItemId = React.useRef<string>();

  const onClickNode = useCallback((nodeId: string) => {
    if (!firstNode && nodeData) {
      const obj = nodeData.find((o) => o.id === nodeId);
      setSelectedItem(obj);
    } else if (firstNode) {
      setSecondNode(nodeId);
    }
  }, [firstNode, nodeData]);

  const onClickLink = useCallback((source: string, target: string) => {
    const obj = {
      source,
      target,
    };
    setSelectedItem(obj);
  }, []);

  const createModeLink = useCallback((id: string) => {
    if (firstNode && firstNode === id) {
      setFirstNode(undefined);
      setSecondNode(undefined);
    } else {
      setFirstNode(id);
    }
  }, [firstNode, setFirstNode, setSecondNode]);

  const onClose = () => {
    setOpenModal(false);
  };

  const onSave = async (name: string, posX: number, posY: number, color: string) => {
    setOpenModal(false);
    try {
      const area = await createArea(study.id, name);
      setNodeData([...nodeData, {
        id: area.id,
        name: area.name,
        x: posX,
        y: posY,
        color,
        rgbColor: color.slice(4, -1).split(',').map(Number),
        size: { width: calculateSize(name), height: NODE_HEIGHT },
      }]);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:createAreaError'), e as AxiosError);
    }
  };

  const getTargetNode = (id: string) => nodeData.find((o) => o.id === id);

  const updateUI = async (id: string, value: UpdateAreaUi) => {
    const targetNode = getTargetNode(id);
    if (targetNode) {
      try {
        const prevColors = targetNode.rgbColor;
        const prevPosition = { x: targetNode.x, y: targetNode.y };
        if ((value.color_rgb[0] !== prevColors[0] || value.color_rgb[1] !== prevColors[1] || value.color_rgb[2] !== prevColors[2]) || (value.x !== prevPosition.x || value.y !== prevPosition.y)) {
          const updateNode = nodeData.filter((o) => o.id !== id);
          setNodeData([...updateNode, {
            ...targetNode,
            x: value.x,
            y: value.y,
            color: `rgb(${value.color_rgb[0]}, ${value.color_rgb[1]}, ${value.color_rgb[2]})`,
            rgbColor: [value.color_rgb[0], value.color_rgb[1], value.color_rgb[2]],
          }]);
          await updateAreaUI(study.id, id, value);
        }
      } catch (e) {
        setNodeData([...nodeData]);
        enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:updateUIError'), e as AxiosError);
      }
    }
  };

  const handleUpdatePosition = async (id: string, x: number, y: number) => {
    const targetNode = getTargetNode(id);
    if (targetNode) {
      updateUI(id, { x, y, color_rgb: targetNode.rgbColor });
    }
  };

  const onDelete = async (id: string, target?: string) => {
    if (graphRef.current) {
      const currentGraph = graphRef.current;
      // eslint-disable-next-line no-underscore-dangle
      currentGraph._setNodeHighlightedValue(id, false);
    }

    setTimeout(async () => {
      if (target && linkData) {
        try {
          const links = linkData.filter((o) => o.source !== id || o.target !== target);
          setLinkData(links);
          setSelectedItem(undefined);
          await deleteLink(study.id, id, target);
        } catch (e) {
          setLinkData([...linkData]);
          enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:deleteAreaOrLink'), e as AxiosError);
        }
      } else if (nodeData && linkData && !target) {
        const obj = nodeData.filter((o) => o.id !== id);
        const links = linkData.filter((o) => o.source !== id && o.target !== id);
        try {
          setSelectedItem(undefined);
          setLinkData(links);
          setNodeData(obj);
          await deleteArea(study.id, id);
        } catch (e) {
          setLinkData([...linkData]);
          setNodeData([...nodeData]);
          enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:deleteAreaOrLink'), e as AxiosError);
        }
      }
    }, 0);
  };

  useEffect(() => {
    const init = async () => {
      if (firstNode && secondNode) {
        try {
          setLinkData([...linkData, ...[{
            source: firstNode,
            target: secondNode,
          }]]);
          setFirstNode(undefined);
          setSecondNode(undefined);
          await createLink(study.id, { area1: firstNode, area2: secondNode });
        } catch (e) {
          setLinkData(linkData.filter((o) => o.source !== firstNode || o.target !== secondNode));
          enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:createLinkError'), e as AxiosError);
        }
      }
    };
    init();
  }, [enqueueSnackbar, t, firstNode, secondNode, study.id, linkData]);

  useEffect(() => {
    const init = async () => {
      try {
        const data = await getSynthesis(study.id);
        const areaData = await getAreaPositions(study.id, Object.keys(data.areas).join(','));
        const areas: AreasConfig = Object.keys(data.areas).length === 1 ? { [Object.keys(data.areas)[0]]: areaData as SingleAreaConfig } : areaData as AreasConfig;
        const tempNodeData = Object.keys(areas).map((areaId) => ({
          id: areaId,
          name: data.areas[areaId].name,
          x: areas[areaId].ui.x,
          y: areas[areaId].ui.y,
          color: `rgb(${areas[areaId].ui.color_r}, ${areas[areaId].ui.color_g}, ${areas[areaId].ui.color_b})`,
          rgbColor: [areas[areaId].ui.color_r, areas[areaId].ui.color_g, areas[areaId].ui.color_b],
          size: { width: calculateSize(areaId), height: NODE_HEIGHT },
        }));
        setNodeData(tempNodeData);
        setLinkData(Object.keys(data.areas).reduce((links, currentAreaId) =>
          links.concat(Object.keys(data.areas[currentAreaId].links).map((linkId) => ({
            source: currentAreaId,
            target: linkId,
          }))), [] as Array<LinkProperties>));
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtoloadstudy'), e as AxiosError);
      } finally {
        setLoaded(true);
      }
    };
    init();
  }, [enqueueSnackbar, study.id, t]);

  useEffect(() => {
    if (selectedItem && isNode(selectedItem)) {
      setSelectedNodeLinks(linkData.filter((o) => o.source === (selectedItem as NodeProperties).id || o.target === (selectedItem as NodeProperties).id));
    }
    if (graphRef.current) {
      const currentGraph = graphRef.current;
      if (prevselectedItemId.current) {
        // eslint-disable-next-line no-underscore-dangle
        currentGraph._setNodeHighlightedValue(prevselectedItemId.current, false);
      }
      if (selectedItem && isNode(selectedItem)) {
        setTimeout(() => {
          // eslint-disable-next-line no-underscore-dangle
          currentGraph._setNodeHighlightedValue((selectedItem as NodeProperties).id, true);
          prevselectedItemId.current = (selectedItem as NodeProperties).id;
        }, 0);
      }
    }
  }, [selectedItem, linkData]);

  return (
    <>
      <SplitLayoutView
        left={
          <MapPropsView item={selectedItem && isNode(selectedItem) ? nodeData.find((o) => o.id === (selectedItem as NodeProperties).id) : selectedItem} setSelectedItem={setSelectedItem} nodeLinks={selectedNodeLinks} nodeList={nodeData} onDelete={onDelete} onArea={() => setOpenModal(true)} updateUI={updateUI} />
        }
        right={(
          <Box
            width="100%"
            height="100%"
            position="relative"
            sx={{ '& svg[name="svg-container-graph-id"]': {
              backgroundColor: '#fefefe',
              backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'8\' height=\'8\' viewBox=\'0 0 8 8\'%3E%3Cg fill=\'%23dedede\' fill-opacity=\'0.4\'%3E%3Cpath fill-rule=\'evenodd\' d=\'M0 0h4v4H0V0zm4 4h4v4H4V4z\'/%3E%3C/g%3E%3C/svg%3E")',
            } }}
          >
            {loaded ? (
              <AutoSizer>
                {
                  ({ height, width }) => (
                    <GraphViewMemo height={height} width={width} nodeData={nodeData} linkData={linkData} onClickLink={onClickLink} onClickNode={onClickNode} graph={graphRef} setSelectedItem={setSelectedItem} onLink={createModeLink} onNodePositionChange={handleUpdatePosition} />
                  )
              }
              </AutoSizer>
            ) : <SimpleLoader />
            }
            <Box width="12%" display="flex" justifyContent="space-between" alignItems="center" position="absolute" right="16px">
              <Typography>
                {`${nodeData.length} ${t('singlestudy:area')}`}
              </Typography>
              <Typography>
                {`${linkData.length} ${t('singlestudy:link')}`}
              </Typography>
            </Box>
          </Box>
        )}
      />
      {openModal && (
        <CreateAreaModal
          open={openModal}
          onClose={onClose}
          onSave={onSave}
        />
      )}
    </>
  );
}

export default Map;
