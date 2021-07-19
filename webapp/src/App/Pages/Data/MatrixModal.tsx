import React, { useState, useEffect } from 'react';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { MatrixInfoDTO, MatrixType } from '../../../common/types';
import InformationModal from '../../../components/ui/InformationModal';
import MatrixView from '../../../components/ui/MatrixView';
import { getMatrix } from '../../../services/api/matrix';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    matrixView: {
      width: '100%',
      height: 'calc(70vh - 100px)',
      padding: theme.spacing(2),
    },
  }));

interface PropTypes {
  matrixInfo: MatrixInfoDTO | undefined;
  open: boolean;
  onClose: () => void;
}

const MatrixModal = (props: PropTypes) => {
  const { matrixInfo, open, onClose } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const classes = useStyles();
  const [matrix, setCurrentMatrix] = useState<MatrixType>({ index: [], columns: [], data: [] });

  useEffect(() => {
    const init = async () => {
      try {
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
        enqueueSnackbar(t('data:matrixError'), { variant: 'error' });
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
      title={`Matrix${matrixInfo ? ` - ${matrixInfo.name}` : ''}`}
      onButtonClick={onClose}
    >
      <div className={classes.matrixView}>
        <MatrixView
          readOnly={false}
          matrix={matrix}
        />
      </div>
    </InformationModal>
  );
};

export default MatrixModal;
