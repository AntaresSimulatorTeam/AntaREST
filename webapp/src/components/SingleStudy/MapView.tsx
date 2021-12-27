import React, { useEffect, useState } from 'react';
import { Graph } from 'react-d3-graph';
import { AxiosError } from 'axios';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
} from '@material-ui/core';
import AutoSizer from 'react-virtualized-auto-sizer';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { getAreaPositions, getSynthesis } from '../../services/api/study';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';

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
  }));

interface Props {
    studyId: string;
}

interface TestStudyConfig {
  archiveInputSeries: Array<string>;
  areas: object;
  bindings: Array<string>;
  enrModelling: string;
  outputPath: string;
  outputs: object;
  path: string;
  sets: object;
  storeNewSet: boolean;
  studyId: string;
  studyPath: string;
  version: number;
}

interface NodeClickConfig {
  id: string;
  x: number;
  y: number;
  color: string;
}

const fakeData = {
  nodes: [
    {
      id: 'aa',
      x: 252 + 300,
      y: 290,
      color: 'rgb(230, 108, 44)',
    },
    {
      id: 'bb',
      x: 415 + 300,
      y: 290,
      color: 'rgb(230, 108, 44)',
    },
    {
      id: 'cc',
      x: 113 + 300,
      y: 199,
      color: 'rgb(230, 108, 44)',
    },
    {
      id: 'dd',
      x: 265 + 300,
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

const NoteView = (props: Props) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { studyId } = props;
  const [studyConfig, setStudyConfig] = useState<TestStudyConfig>();
  const [areasList, setAreasList] = useState<string>();
  const [areas, setAreas] = useState<string>();
  const [loaded, setLoaded] = useState(false);
  const [nodeClick, setNodeClick] = useState<NodeClickConfig>();
  const { enqueueSnackbar } = useSnackbar();

  const onClickNode = (nodeId: string) => {
    const obj = fakeData.nodes.find((o) => o.id === nodeId);
    setNodeClick(obj);
  };

  const onClickLink = (source: string, target: string) => {
    console.log(`Clicked link between ${source} and ${target}`);
  };

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
      const test = studyConfig;
      console.log(studyConfig);
      let areaList = '';
      if (test) {
        Object.keys(test.areas).map((key) => {
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
        <Typography className={classes.title}>Map</Typography>
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
                  staticGraph: true,
                  d3: {
                  },
                  node: {
                    color: '#d3d3d3',
                    size: 600,
                    fontSize: 15,
                  },
                  link: {
                    color: '#d3d3d3',
                    strokeWidth: 4,
                  },
                }}
                onClickNode={onClickNode}
                onClickLink={onClickLink}
              />
            )
          }
        </AutoSizer>
        {nodeClick && (
        <Card className={classes.popup}>
          <CardContent>
            <Typography gutterBottom>
              Area
            </Typography>
            <Typography variant="h5" component="h2">
              {nodeClick.id}
            </Typography>
            <Typography variant="body2" component="p">
              {nodeClick.x}
              <br />
              {nodeClick.y}
              <br />
              {nodeClick.color}
            </Typography>
          </CardContent>
          <CardActions>
            <Button size="small">More</Button>
            <Button onClick={() => setNodeClick(undefined)} size="small">Close</Button>
          </CardActions>
        </Card>
        )}
      </div>
    </Paper>
  );
};

export default NoteView;
