/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { useSnackbar } from 'notistack';
import { Translation } from 'react-i18next';
import { getStudyData } from '../../../services/api/study';
import MainContentLoader from '../../ui/loaders/MainContentLoader';
import {MatrixType} from "../../../common/types";
import MatrixView from "./MatrixView";

interface PropTypes {
  study: string;
  url: string;
}

const StudyMatrixView = (props: PropTypes) => {
  const { study, url } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [data, setData] = useState<MatrixType>();
  const [loaded, setLoaded] = useState(false);

  const loadFileData = async () => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = await getStudyData(study, url);
      if (typeof res === 'string') {
        const fixed = res.replace(/NaN/g, '"NaN"');
        setData(JSON.parse(fixed));
      } else {
        setData(res);
      }
    } catch (e) {
      enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
    } finally {
      setLoaded(true);
    }
  };

  useEffect(() => {
    const urlParts = url.split('/');
    if (urlParts.length < 2) {
      enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
      return;
    }
    loadFileData();
  }, [url]);

  return (
    <>
      {data && Object.keys(data).length > 0 && <MatrixView data={data}/>}
      {!loaded && (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
          <MainContentLoader />
        </div>
      )}
    </>
  );
};

export default StudyMatrixView;