import React, { useEffect, useState } from 'react';
import { Graph } from 'react-d3-graph';
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

const fakeData = {
  nodes: [{ id: 'Harry' }, { id: 'Sally' }, { id: 'Alice' }],
  links: [
    { source: 'Harry', target: 'Sally' },
    { source: 'Harry', target: 'Alice' },
  ],
};

const NoteView = (props: Props) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { studyId } = props;
  const [studyConfig, setStudyConfig] = useState<TestStudyConfig>();
  const [areasList, setAreasList] = useState<string>();
  const [areas, setAreas] = useState<string>();
  const [loaded, setLoaded] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const onClickNode = (nodeId: string) => {
    console.log(`Clicked node ${nodeId}`);
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
      let areaList = '';
      if (test) {
        Object.keys(test.areas).map((key) => {
          areaList += `${key},`;
          return areaList;
        });
      }
      setAreasList(areaList.replace(/&/g, '%26').substring(0, areaList.length - 2));
    }
  }, [loaded, studyConfig, enqueueSnackbar, t]);

  useEffect(() => {
    const init = async () => {
      try {
        if (areasList) {
          console.log(areasList);
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
                  d3: {
                    linkLength: 500,
                  },
                  node: {
                    color: '#d3d3d3',
                    size: 500,
                    fontSize: 15,
                  },
                  link: {
                    color: '#d3d3d3',
                  },
                }}
                onClickNode={onClickNode}
                onClickLink={onClickLink}
              />
            )
          }
        </AutoSizer>
      </div>
    </Paper>
  );
};

export default NoteView;
