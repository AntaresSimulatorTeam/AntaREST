import React, { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme, Tooltip } from '@material-ui/core';
import { MatrixInfoDTO, MatrixType } from '../../common/types';
import InformationModal from '../ui/InformationModal';
import MatrixView from '../ui/MatrixView';
import { getMatrix } from '../../services/api/matrix';
import { CopyIcon } from './utils';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import SimpleLoader from '../ui/loaders/SimpleLoader';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    matrixView: {
      width: '100%',
      height: '100%',
      padding: theme.spacing(2),
      position: 'relative',
    },
  }));

interface PropTypes {
  matrixInfo: MatrixInfoDTO;
  open: boolean;
  onClose: () => void;
}

const MatrixModal = (props: PropTypes) => {
  const { matrixInfo, open, onClose } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const classes = useStyles();
  const [loading, setLoading] = useState(false);
  const [matrix, setCurrentMatrix] = useState<MatrixType>({ index: [], columns: [], data: [] });

  const copyId = (matrixId: string): void => {
    try {
      navigator.clipboard.writeText(matrixId);
      enqueueSnackbar(t('data:onMatrixIdCopySuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('data:onMatrixIdCopyError'), { variant: 'error' });
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        if (matrixInfo) {
          const res = await getMatrix(matrixInfo.id);
          const matrixContent: MatrixType = {
            index: matrix ? res.index : [],
            columns: matrix ? res.columns : [],
            data: matrix ? res.data : [],
          };
          setCurrentMatrix(matrixContent);
        }
      } catch (error) {
        enqueueErrorSnackbar(enqueueSnackbar, t('data:matrixError'), error as AxiosError);
      } finally {
        setLoading(false);
      }
    };
    init();
    return () => {
      setCurrentMatrix({ index: [], columns: [], data: [] });
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enqueueSnackbar, matrixInfo, t]);

  return (
    <InformationModal
      open={open}
      fixedSize
      title={(
        <div>
          <Tooltip title={matrixInfo.id} placement="top">
            <span>{`Matrix- ${matrixInfo.name}`}</span>
          </Tooltip>
          <Tooltip title={t('data:copyid') as string} placement="top">
            <CopyIcon style={{ marginLeft: '0.5em', cursor: 'pointer' }} onClick={() => copyId(matrixInfo.id)} />
          </Tooltip>
        </div>
      )}
      onButtonClick={onClose}
      buttonName={t('main:closeButton')}
    >
      <div className={classes.matrixView}>
        {
          loading && <SimpleLoader />
        }
        <MatrixView
          readOnly={false}
          matrix={matrix}
        />
      </div>
    </InformationModal>
  );
};

export default MatrixModal;
