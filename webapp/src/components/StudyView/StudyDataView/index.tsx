import React from 'react';
import { makeStyles, Theme, createStyles } from '@material-ui/core';
import StudyFileView from './StudyFileView';
import StudyJsonView from './StudyJsonView';
import StudyMatrixView from './StudyMatrixView';
import { StudyDataType } from '../../../common/types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flexGrow: 1,
    padding: theme.spacing(2),
  },
}));

type DataType = {path: string; json: string};
interface PropTypes {
  study: string;
  type: StudyDataType;
  data: string | DataType;
  studyData: any;
  setStudyData: (elm: any) => void;
}

interface RenderData {
  css: React.CSSProperties;
  data: JSX.Element;
}

const StudyDataView = (props: PropTypes) => {
  const { study, type, data, studyData, setStudyData } = props;
  const classes = useStyles();
  const filterOut = ['output', 'logs', 'Desktop'];

  const renderData = (): RenderData => {
    if (type === 'file') {
      return { css: { overflow: 'auto' }, data: <StudyFileView study={study} url={data as string} filterOut={filterOut} /> };
    }
    if (type === 'matrix' || type === 'matrixfile') {
      return { css: { overflow: 'auto' }, data: <StudyMatrixView study={study} url={data as string} filterOut={filterOut}/> };
    }
    return { css: { overflow: 'hidden', paddingTop: '0px' }, data: <StudyJsonView studyData={studyData} setStudyData={setStudyData} study={study} data={data as DataType} filterOut={filterOut} /> };
  };

  const rd = renderData();
  return (
    <div className={classes.root} style={rd.css}>
      {rd.data}
    </div>
  );
};

export default StudyDataView;
