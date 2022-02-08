import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Graph, GraphLink, GraphNode } from 'react-d3-graph';
import { AxiosError } from 'axios';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
} from '@material-ui/core';
import AutoSizer from 'react-virtualized-auto-sizer';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { getAreaPositions, getSynthesis } from '../../../services/api/study';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import { NodeProperties, LinkProperties, AreasConfig, SingleAreaConfig, UpdateAreaUi, isNode } from './types';
import CreateAreaModal from './CreateAreaModal';
import PropertiesView from './PropertiesView';
import SimpleLoader from '../../ui/loaders/SimpleLoader';
import { StudyMetadata } from '../../../common/types';
import GraphView from './GraphView';
import { createArea, createLink, deleteArea, deleteLink, updateAreaUI } from '../../../services/api/studydata';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: 'white',
      margin: theme.spacing(1),
      boxSizing: 'border-box',
    },
    header: {
      width: '100%',
      height: '40px',
      boxSizing: 'border-box',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
      borderTopLeftRadius: theme.shape.borderRadius,
      borderTopRightRadius: theme.shape.borderRadius,
      paddingLeft: theme.spacing(2),
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
    },
    autosizer: {
      display: 'block',
      width: '80%',
      height: '100%',
      position: 'relative',
    },
    popup: {
      position: 'absolute',
      right: '30px',
      top: '100px',
      width: '200px',
    },
    graph: {
      '& svg[name="svg-container-graph-id"]': {
        backgroundColor: '#fefefe',
        backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'8\' height=\'8\' viewBox=\'0 0 8 8\'%3E%3Cg fill=\'%23dedede\' fill-opacity=\'0.4\'%3E%3Cpath fill-rule=\'evenodd\' d=\'M0 0h4v4H0V0zm4 4h4v4H4V4z\'/%3E%3C/g%3E%3C/svg%3E")',
      },
    },
    graphView: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      width: '100%',
      height: '100%',
    },
    areaCount: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      width: '12%',
      position: 'absolute',
      right: theme.spacing(2),
    },
  }));

interface Props {
    study: StudyMetadata;
}

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

const MapView = (props: Props) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { study } = props;
  const [loaded, setLoaded] = useState(false);
  const [selectedItem, setSelectedItem] = useState<NodeProperties | LinkProperties>();
  const [selectedNodeLinks, setSelectedNodeLinks] = useState<Array<LinkProperties>>();
  const [nodeData, setNodeData] = useState<Array<NodeProperties>>([]);
  const [linkData, setLinkData] = useState<Array<LinkProperties>>([]);
  const { enqueueSnackbar } = useSnackbar();
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [firstNode, setFirstNode] = useState<string>();
  const [secondNode, setSecondNode] = useState<string>();
  const graphRef = useRef<Graph<GraphNode & NodeProperties, GraphLink & LinkProperties>>(null);
  const prevselectedItemId = useRef<string>();
  // const [zoom, setZoom] = useState<number>();

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
      await createArea(study.id, name);
      setNodeData([...nodeData, {
        id: name,
        x: posX,
        y: posY,
        color,
        rgbColor: color.slice(4, -1).split(',').map(Number),
        size: { width: calculateSize(name), height: NODE_HEIGHT },
      }]);
    } catch (e) {
      setNodeData(nodeData.filter((o) => o.id !== name));
      enqueueErrorSnackbar(enqueueSnackbar, 'Creation marche pas', e as AxiosError);
    }
  };

  const handleUpdate = async (id: string, value: UpdateAreaUi) => {
    try {
      const filterNodes = nodeData.find((o) => o.id === id);
      if (filterNodes) {
        const prevColors = filterNodes.rgbColor;
        if (value.color_rgb[0] !== prevColors[0] || value.color_rgb[1] !== prevColors[1] || value.color_rgb[2] !== prevColors[2]) {
          const updateNode = nodeData.filter((o) => o.id !== id);
          setNodeData([...updateNode, {
            id,
            x: value.x,
            y: value.y,
            color: `rgb(${value.color_rgb[0]}, ${value.color_rgb[1]}, ${value.color_rgb[2]})`,
            rgbColor: filterNodes.rgbColor,
            size: { width: calculateSize(id), height: NODE_HEIGHT },
          }]);
          await updateAreaUI(study.id, id, value);
        }
      }
    } catch (e) {
      // setNodeData(nodeData.filter((o) => o.id !== id));
      enqueueErrorSnackbar(enqueueSnackbar, 'Color update marche pas', e as AxiosError);
    }
  };

  const handleUpdatePosition = async (id: string, x: number, y: number) => {
    try {
      const filterNodes = nodeData.find((o) => o.id === id);
      if (filterNodes) {
        const prevPosition = { x: nodeData.find((o) => o.id === id)?.x, y: nodeData.find((o) => o.id === id)?.y };
        if (x !== prevPosition.x || y !== prevPosition.y) {
          const updateNode = nodeData.filter((o) => o.id !== id);
          setNodeData([...updateNode, {
            id,
            x: Math.floor(x),
            y: Math.floor(y),
            color: filterNodes.color,
            rgbColor: filterNodes.rgbColor,
            size: { width: calculateSize(id), height: NODE_HEIGHT },
          }]);
          // eslint-disable-next-line @typescript-eslint/camelcase
          await updateAreaUI(study.id, id, { x, y, color_rgb: filterNodes.rgbColor });
        }
      }
    } catch (e) {
      // setNodeData(nodeData.filter((o) => o.id !== id));
      enqueueErrorSnackbar(enqueueSnackbar, 'Position Update marche pas', e as AxiosError);
    }
  };

  const onDelete = async (id: string, target?: string) => {
    try {
      if (graphRef.current) {
        const currentGraph = graphRef.current;
        // eslint-disable-next-line no-underscore-dangle
        currentGraph._setNodeHighlightedValue(id, false);
      }

      setTimeout(async () => {
        if (target && linkData) {
          const links = linkData.filter((o) => o.source !== id || o.target !== target);
          setLinkData(links);
          setSelectedItem(undefined);
          await deleteLink(study.id, id, target);
        }
      }, 0);

      setTimeout(async () => {
        if (nodeData && linkData && !target) {
          setSelectedItem(undefined);
          const obj = nodeData.filter((o) => o.id !== id);
          const links = linkData.filter((o) => o.source !== id && o.target !== id);
          setLinkData(links);
          setNodeData(obj);
          await deleteArea(study.id, id);
        }
      }, 0);
    } catch (e) {
      if (target && linkData) {
        setLinkData([...linkData, ...[{
          source: id,
          target,
        }]]);
      }
      enqueueErrorSnackbar(enqueueSnackbar, 'delete marche pas', e as AxiosError);
    }
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
          enqueueErrorSnackbar(enqueueSnackbar, 'lien marche pas', e as AxiosError);
        }
      }
    };
    init();
  }, [enqueueSnackbar, firstNode, secondNode, study.id, linkData]);

  useEffect(() => {
    const init = async () => {
      try {
        const data = await getSynthesis(study.id);
        setLinkData(Object.keys(data.areas).reduce((links, currentAreaId) =>
          links.concat(Object.keys(data.areas[currentAreaId].links).map((linkId) => ({
            source: currentAreaId,
            target: linkId,
          }))), [] as Array<LinkProperties>));
        const areaData = await getAreaPositions(study.id, Object.keys(data.areas).join(','));
        if (Object.keys(data.areas).length === 1) {
          const area = { [Object.keys(data.areas)[0]]: areaData as SingleAreaConfig };
          const tempNodeData = Object.keys(area).map((areaId) => ({
            id: areaId,
            x: area[areaId].ui.x,
            y: area[areaId].ui.y,
            color: `rgb(${area[areaId].ui.color_r}, ${area[areaId].ui.color_g}, ${area[areaId].ui.color_b})`,
            rgbColor: [area[areaId].ui.color_r, area[areaId].ui.color_g, area[areaId].ui.color_b],
            size: { width: calculateSize(areaId), height: NODE_HEIGHT },
          }));
          setNodeData(tempNodeData);
        } else {
          const area = areaData as AreasConfig;
          const tempNodeData = Object.keys(area).map((areaId) => ({
            id: areaId,
            x: area[areaId].ui.x,
            y: area[areaId].ui.y,
            color: `rgb(${area[areaId].ui.color_r}, ${area[areaId].ui.color_g}, ${area[areaId].ui.color_b})`,
            rgbColor: [area[areaId].ui.color_r, area[areaId].ui.color_g, area[areaId].ui.color_b],
            size: { width: calculateSize(areaId), height: NODE_HEIGHT },
          }));
          setNodeData(tempNodeData);
        }
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
    <Paper className={classes.root}>
      <div className={classes.header}>
        <Typography className={classes.title}>{t('singlestudy:map')}</Typography>
      </div>
      <div className={classes.graphView}>
        <PropertiesView item={selectedItem && isNode(selectedItem) ? nodeData.find((o) => o.id === (selectedItem as NodeProperties).id) : selectedItem} setSelectedItem={setSelectedItem} nodeLinks={selectedNodeLinks} nodeList={nodeData} onDelete={onDelete} onArea={() => setOpenModal(true)} onBlur={handleUpdate} />
        <div className={`${classes.autosizer} ${classes.graph}`}>
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
          <div className={classes.areaCount}>
            <p>
              {`${nodeData.length} ${t('singlestudy:area')}`}
            </p>
            <p>
              {`${linkData.length} ${t('singlestudy:link')}`}
            </p>
          </div>
        </div>
      </div>
      {openModal && (
        <CreateAreaModal
          open={openModal}
          onClose={onClose}
          onSave={onSave}
        />
      )}
    </Paper>
  );
};

export default MapView;
