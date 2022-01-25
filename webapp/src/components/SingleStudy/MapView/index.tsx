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
import { NodeProperties, LinkProperties, StudyProperties, AreasConfig, SingleAreaConfig, ColorProperties } from './types';
import CreateAreaModal from './CreateAreaModal';
import PropertiesView from './PropertiesView';
import SimpleLoader from '../../ui/loaders/SimpleLoader';
import { StudyMetadata } from '../../../common/types';
import GraphView from './GraphView';

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

const calculateSize = (text: string): number => {
  const textSize = text.length;
  if (textSize === 1) {
    return FONT_SIZE * textSize * 32;
  }
  if (textSize <= 2) {
    return FONT_SIZE * textSize * 16;
  }
  if (textSize <= 5) {
    return FONT_SIZE * textSize * 10;
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
  const [studyConfig, setStudyConfig] = useState<StudyProperties>();
  const [areas, setAreas] = useState<AreasConfig>();
  const [loaded, setLoaded] = useState(false);
  const [selectedItem, setSelectedItem] = useState<NodeProperties | LinkProperties>();
  const [selectedNodeLinks, setSelectedNodeLinks] = useState<Array<LinkProperties>>();
  const [nodeData, setNodeData] = useState<Array<NodeProperties>>([]);
  const [linkData, setLinkData] = useState<Array<LinkProperties>>([]);
  const { enqueueSnackbar } = useSnackbar();
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [createLinkMode, setCreateLinkMode] = useState<boolean>(false);
  const [firstNode, setFirstNode] = useState<string>();
  const [secondNode, setSecondNode] = useState<string>();
  const graphRef = useRef<Graph<GraphNode & NodeProperties, GraphLink & LinkProperties>>(null);
  const prevselectedItemId = useRef<string>();
  const [colors, setColors] = useState<Array<ColorProperties>>([]);
  // const [zoom, setZoom] = useState<number>();

  const onClickNode = useCallback((nodeId: string) => {
    if (!createLinkMode && nodeData) {
      const obj = nodeData.find((o) => o.id === nodeId);
      setSelectedItem(obj);
    } else if (!firstNode) {
      setFirstNode(nodeId);
    } else if (firstNode) {
      setSecondNode(nodeId);
    }
  }, [createLinkMode, firstNode, nodeData]);

  useEffect(() => {
    if (selectedItem && Object.keys(selectedItem)[0] === 'id') {
      setSelectedNodeLinks(linkData.filter((o) => o.source === (selectedItem as NodeProperties).id || o.target === (selectedItem as NodeProperties).id));
    }
    if (graphRef.current) {
      const currentGraph = graphRef.current;
      if (prevselectedItemId.current) {
        // eslint-disable-next-line no-underscore-dangle
        currentGraph._setNodeHighlightedValue(prevselectedItemId.current, false);
      }
      if (selectedItem && Object.keys(selectedItem)[0] === 'id') {
        setTimeout(() => {
          // eslint-disable-next-line no-underscore-dangle
          currentGraph._setNodeHighlightedValue((selectedItem as NodeProperties).id, true);
          prevselectedItemId.current = (selectedItem as NodeProperties).id;
        }, 0);
      }
    }
  }, [selectedItem, linkData]);

  const onClickLink = useCallback((source: string, target: string) => {
    const obj = {
      source,
      target,
    };
    setSelectedItem(obj);
  }, []);

  const createLink = () => {
    if (createLinkMode) {
      setCreateLinkMode(false);
      setFirstNode(undefined);
      setSecondNode(undefined);
    } else {
      setCreateLinkMode(true);
    }
  };

  const onClose = () => {
    setOpenModal(false);
  };

  const onSave = (name: string, posX: number, posY: number, color: string) => {
    setOpenModal(false);
    if (nodeData) {
      nodeData.push({
        id: name,
        x: posX,
        y: posY,
        color,
      });
    }
  };

  const onDelete = (id: string, target?: string) => {
    if (target && linkData) {
      const obj = linkData.find((o) => o.source === id && o.target === target);
      if (obj) {
        const i = linkData.indexOf(obj);
        if (i !== -1) {
          linkData.splice(i, 1);
          setSelectedItem(undefined);
        }
      }
    }
    if (nodeData && linkData && !target) {
      const obj = nodeData.find((o) => o.id === id);
      const links = linkData.filter((o) => o.source === id || o.target === id);
      if (obj) {
        const i = nodeData.indexOf(obj);
        if (i !== -1) {
          nodeData.splice(i, 1);
          setSelectedItem(undefined);
        }
      }
      if (links) {
        // eslint-disable-next-line array-callback-return
        for (let i = 0; i < links.length; i += 1) {
          const index = linkData.indexOf(links[i]);
          if (index !== -1) {
            linkData.splice(index, 1);
          }
        }
      }
    }
  };

  useEffect(() => {
    if (firstNode && secondNode && linkData) {
      linkData.push({
        source: firstNode,
        target: secondNode,
      });
      setCreateLinkMode(false);
      setFirstNode(undefined);
      setSecondNode(undefined);
    }
  }, [setCreateLinkMode, firstNode, secondNode, linkData]);

  useEffect(() => {
    const init = async () => {
      try {
        const data = await getSynthesis(study.id);
        setStudyConfig(data as StudyProperties);
        const areaData = await getAreaPositions(study.id, Object.keys(data.areas).join(','));
        if (Object.keys(data.areas).length === 1) {
          setAreas({
            [Object.keys(data.areas)[0]]: areaData as SingleAreaConfig,
          });
        } else {
          setAreas(areaData as AreasConfig);
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
    if (areas) {
      const tempNodeData = Object.keys(areas).map((areaId) => ({
        id: areaId,
        x: areas[areaId].ui.x,
        y: areas[areaId].ui.y,
        color: `rgb(${areas[areaId].ui.color_r}, ${areas[areaId].ui.color_g}, ${areas[areaId].ui.color_b})`,
        size: { width: calculateSize(areaId), height: 320 },
      }));

      const colorsRGB = Object.keys(areas).map((areaId) => ({
        id: areaId,
        r: areas[areaId].ui.color_r,
        g: areas[areaId].ui.color_g,
        b: areas[areaId].ui.color_b,
      }));

      setNodeData(tempNodeData);
      setColors(colorsRGB);

      if (studyConfig) {
        setLinkData(Object.keys(studyConfig.areas).reduce((links, currentAreaId) =>
          links.concat(Object.keys(studyConfig.areas[currentAreaId].links).map((linkId) => ({
            source: currentAreaId,
            target: linkId,
          }))), [] as Array<LinkProperties>));
      }
    }
  }, [areas, studyConfig]);

  return (
    <Paper className={classes.root}>
      <div className={classes.header}>
        <Typography className={classes.title}>{t('singlestudy:map')}</Typography>
      </div>
      <div className={classes.graphView}>
        <PropertiesView item={selectedItem} setSelectedItem={setSelectedItem} nodeLinks={selectedNodeLinks} nodeList={nodeData} onClose={() => setSelectedItem(undefined)} onDelete={onDelete} onArea={() => setOpenModal(true)} onLink={createLink} />
        <div className={`${classes.autosizer} ${classes.graph}`}>
          {loaded ? (
            <AutoSizer>
              {
                ({ height, width }) => {
                  console.log('Rendering with');
                  return (
                    <GraphViewMemo height={height} width={width} nodeData={nodeData} linkData={linkData} onClickLink={onClickLink} onClickNode={onClickNode} graph={graphRef} colors={colors} setSelectedItem={setSelectedItem} />
                  );
                }
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
