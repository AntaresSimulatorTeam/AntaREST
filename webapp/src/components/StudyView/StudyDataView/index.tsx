import React from 'react';
import { makeStyles, Theme, createStyles } from '@material-ui/core';
import StudyFileView from './StudyFileView';
import StudyJsonView from './StudyJsonView';
import StudyMatrixView from './StudyMatrixView';
import { StudyDataType } from '../../../common/types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      flexGrow: 1,
      padding: theme.spacing(2),
    },
  }));

interface PropTypes {
  study: string;
  type: StudyDataType;
  data: string;
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

  const refreshView = () => {
    setStudyData({ ...studyData });
  };

  const renderData = (): RenderData => {
    if (type === 'file') {
      return {
        css: { overflow: 'auto' },
        data: (
          <StudyFileView study={study} url={data} filterOut={filterOut} refreshView={refreshView} />
        ),
      };
    }
    if (type === 'matrix' || type === 'matrixfile') {
      return {
        css: { overflow: 'auto' },
        data: (
          <StudyMatrixView
            study={study}
            url={data}
            filterOut={filterOut}
            refreshView={refreshView}
          />
        ),
      };
    }
    return {
      css: { overflow: 'hidden', paddingTop: '0px' },
      data: (
        <StudyJsonView study={study} data={data} filterOut={filterOut} />
      ),
    };
  };

  const rd = renderData();
  return (
    <div className={classes.root} style={rd.css}>
      {rd.data}
    </div>
  );
};

export default StudyDataView;
