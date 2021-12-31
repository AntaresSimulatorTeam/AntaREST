import React, { useEffect, useState } from 'react';
import { Graph } from 'react-d3-graph';
import { AxiosError } from 'axios';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
  Button,
} from '@material-ui/core';
import AutoSizer from 'react-virtualized-auto-sizer';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { getAreaPositions, getSynthesis } from '../../../services/api/study';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import PanelCardView from './PanelCardView';
import { NodeClickConfig, LinkClickConfig, TestStudyConfig } from './types';
import CreateAreaModal from './CreateAreaModal';

const buttonStyle = (theme: Theme, color: string) => ({
  width: '120px',
  border: `2px solid ${color}`,
  color,
  margin: theme.spacing(0.5),
  '&:hover': {
    color: 'white',
    backgroundColor: color,
  },
});

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
      width: '100%',
      height: '100%',
      position: 'relative',
    },
    popup: {
      position: 'absolute',
      right: '30px',
      top: '100px',
      width: '200px',
    },
    button: {
      position: 'absolute',
      left: '10px',
      bottom: '10px',
      ...buttonStyle(theme, theme.palette.primary.main),
      boxSizing: 'border-box',
    },
    button2: {
      position: 'absolute',
      left: '150px',
      bottom: '10px',
      ...buttonStyle(theme, theme.palette.primary.main),
      boxSizing: 'border-box',
    },
  }));

interface Props {
    studyId: string;
}

const fakeData = {
  nodes: [
    {
      id: 'aa',
      x: 252,
      y: 290,
      color: 'rgb(230, 108, 44)',
    },
    {
      id: 'bb',
      x: 415,
      y: 290,
      color: 'rgb(230, 108, 44)',
    },
    {
      id: 'cc',
      x: 113,
      y: 199,
      color: 'rgb(230, 108, 44)',
    },
    {
      id: 'dd',
      x: 265,
      y: 199,
      color: 'rgb(230, 108, 44)',
    }],
  links: [
    { source: 'aa', target: 'bb' },
    { source: 'aa', target: 'cc' },
    { source: 'aa', target: 'dd' },
  ],
};

/*

& psp x1,& psp x2,& psp y,& psp-hub,& psp-in,& psp-out,aa,bb,cc,dd,east,ee,ff,gg,hh,hydro node 1,hydro node-2,hydro node-3,ii,jj,kk,ll,mm,nn,north,oo,pp,qq,rr,solar gen node,south,ss,tt,thermal,uu,vv,west,wind power 1,wind power-2,wind power-3,ww,wind 6000,wind 9000,xx,yy,z MapView.tsx:143
aa {

ee {
  "x": 265,
  "y": 199,
  "color_r": 230,
  "color_g": 108,
  "color_b": 44,
  "layers": "0 8"
}
xx {
  "x": 397,
  "y": -275,
  "color_r": 230,
  "color_g": 108,
  "color_b": 44,
  "layers": "0 8"
}
yy {
  "x": 319,
  "y": -351,
  "color_r": 230,
  "color_g": 108,
  "color_b": 44,
  "layers": "0 8"
}
*/

const MapView = (props: Props) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { studyId } = props;
  const [studyConfig, setStudyConfig] = useState<TestStudyConfig>();
  const [areasList, setAreasList] = useState<string>();
  const [areas, setAreas] = useState<string>();
  const [loaded, setLoaded] = useState(false);
  const [nodeClick, setNodeClick] = useState<NodeClickConfig>();
  const [linkClick, setLinkClick] = useState<LinkClickConfig>();
  const { enqueueSnackbar } = useSnackbar();
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [createLinkMode, setCreateLinkMode] = useState<boolean>(false);
  const [firstNode, setFirstNode] = useState<string>();
  const [secondNode, setSecondNode] = useState<string>();

  const onClickNode = (nodeId: string) => {
    if (!createLinkMode) {
      const obj = fakeData.nodes.find((o) => o.id === nodeId);
      setNodeClick(obj);
      setLinkClick(undefined);
    } else if (!firstNode) {
      setFirstNode(nodeId);
    } else if (firstNode) {
      setSecondNode(nodeId);
    }
  };

  const onClickLink = (source: string, target: string) => {
    const obj = {
      source,
      target,
    };
    setLinkClick(obj);
    setNodeClick(undefined);
  };

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
    fakeData.nodes.push({
      id: name,
      x: posX,
      y: posY,
      color,
    });
  };

  const onDelete = (id: string, target?: string) => {
    if (target) {
      const obj = fakeData.links.find((o) => o.source === id && o.target === target);
      if (obj) {
        const i = fakeData.links.indexOf(obj);
        if (i !== -1) {
          fakeData.links.splice(i, 1);
          setLinkClick(undefined);
        }
      }
    } else {
      const obj = fakeData.nodes.find((o) => o.id === id);
      if (obj) {
        const i = fakeData.nodes.indexOf(obj);
        if (i !== -1) {
          fakeData.nodes.splice(i, 1);
          setNodeClick(undefined);
        }
      }
    }
  };

  useEffect(() => {
    if (firstNode && secondNode) {
      fakeData.links.push({
        source: firstNode,
        target: secondNode,
      });
      setCreateLinkMode(false);
      setFirstNode(undefined);
      setSecondNode(undefined);
    }
  }, [setCreateLinkMode, firstNode, secondNode]);

  useEffect(() => {
    const init = async () => {
      try {
        const data = await getSynthesis(studyId);
        setStudyConfig(data as TestStudyConfig);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtoloadstudy'), e as AxiosError);
      } finally {
        setLoaded(true);
      }
    };
    init();
  }, [enqueueSnackbar, studyId, t]);

  useEffect(() => {
    if (loaded) {
      let areaList = '';
      if (studyConfig) {
        Object.keys(studyConfig.areas).map((key) => {
          areaList += `${key},`;
          return areaList;
        });
      }
      setAreasList(areaList.substring(0, areaList.length - 2));
    }
  }, [loaded, studyConfig, enqueueSnackbar, t]);

  useEffect(() => {
    const init = async () => {
      try {
        if (areasList) {
          const data = await getAreaPositions(studyId, areasList);
          setAreas(data);
        }
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtoloadstudy'), e as AxiosError);
      }
    };
    init();
  }, [studyId, areasList, enqueueSnackbar, t]);

  console.log(areas);

  return (
    <Paper className={classes.root}>
      <div className={classes.header}>
        <Typography className={classes.title}>{t('singlestudy:map')}</Typography>
      </div>
      <div className={classes.autosizer}>
        <AutoSizer>
          {
            ({ height, width }) => (
              <Graph
                id="graph-id" // id is mandatory
                data={fakeData}
                config={{
                  height,
                  width,
                  staticGraphWithDragAndDrop: true,
                  initialZoom: 1.5,
                  d3: {
                  },
                  node: {
                    color: '#d3d3d3',
                    size: 600,
                    fontSize: 15,
                  },
                  link: {
                    color: '#d3d3d3',
                    strokeWidth: 2,
                  },
                }}
                onClickNode={onClickNode}
                onClickLink={onClickLink}
              />
            )
          }
        </AutoSizer>

        <Button className={classes.button} onClick={() => setOpenModal(true)}>
          {t('singlestudy:newArea')}
        </Button>
        <Button className={classes.button2} onClick={createLink}>
          {t('singlestudy:newLink')}
        </Button>

        {nodeClick && (
          <PanelCardView name={t('singlestudy:area')} node={nodeClick} onClose={() => setNodeClick(undefined)} onDelete={onDelete} />
        )}

        {linkClick && (
          <PanelCardView name={t('singlestudy:link')} link={linkClick} onClose={() => setLinkClick(undefined)} onDelete={onDelete} />
        )}
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
