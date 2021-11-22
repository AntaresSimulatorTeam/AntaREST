import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import ContentLoader from 'react-content-loader';
import { AxiosError } from 'axios';
import { makeStyles, createStyles } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../App/reducers';
import GenericListingView from '../ui/NavComponents/GenericListingView';
import DataView from './DataView';
import { deleteDataSet, getMatrixList } from '../../services/api/matrix';
import { MatrixDataSetDTO, IDType, MatrixInfoDTO } from '../../common/types';
import DataModal from './DataModal';
import ConfirmationModal from '../ui/ConfirmationModal';
import MatrixModal from './MatrixModal';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';

const useStyles = makeStyles(() =>
  createStyles({
    contentloader: {
      width: '100%',
      height: '100%',
    },
    contentloader1: {
      width: '100%',
      height: '100%',
      zIndex: 0,
      position: 'absolute',
    },
    contentloader2: {
      width: '100%',
      height: '100%',
      zIndex: 10,
      position: 'absolute',
    },
  }));
const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const Data = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const classes = useStyles();
  const [dataList, setDataList] = useState<Array<MatrixDataSetDTO>>([]);
  const [idForDeletion, setIdForDeletion] = useState<IDType>(-1);
  const [filter, setFilter] = useState<string>('');
  const { user } = props;
  const [loaded, setLoaded] = useState(false);

  // User modal
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [matrixModal, setMatrixModal] = useState<boolean>(false);
  const [currentData, setCurrentData] = useState<MatrixDataSetDTO|undefined>();
  const [currentMatrix, setCurrentMatrix] = useState<MatrixInfoDTO|undefined>();

  const createNewData = () => {
    setCurrentData(undefined);
    setOpenModal(true);
  };

  const onUpdateClick = (id: IDType): void => {
    setCurrentData(dataList.find((item) => item.id === id));
    setOpenModal(true);
  };

  const onDeleteClick = (id: IDType) => {
    setIdForDeletion(id);
    setOpenConfirmationModal(true);
  };

  const manageDataDeletion = async () => {
    try {
      await deleteDataSet(idForDeletion as string);
      setDataList(dataList.filter((item) => item.id !== idForDeletion));
      enqueueSnackbar(t('data:onMatrixDeleteSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('data:onMatrixDeleteError'), e as AxiosError);
    }
    setIdForDeletion(-1);
    setOpenConfirmationModal(false);
  };

  const onModalClose = () => {
    setOpenModal(false);
  };

  const onMatrixModalClose = () => {
    setCurrentMatrix(undefined);
    setMatrixModal(false);
  };

  const onNewDataUpdate = (newData: MatrixDataSetDTO): void => {
    const tmpList = ([] as Array<MatrixDataSetDTO>).concat(dataList);
    const index = tmpList.findIndex((elm) => elm.id === newData.id);
    if (index >= 0) {
      tmpList[index] = newData;
      setDataList(tmpList);
    } else {
      setDataList(dataList.concat(newData));
    }
  };

  const onMatrixClick = async (matrixInfo: MatrixInfoDTO) => {
    setCurrentMatrix(matrixInfo);
    setMatrixModal(true);
  };

  useEffect(() => {
    const init = async () => {
      try {
        const matrix = await getMatrixList();
        setDataList(matrix);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('data:matrixError'), e as AxiosError);
      } finally {
        setLoaded(true);
      }
    };
    init();
    return () => {
      setDataList([]);
    };
  }, [user, t, enqueueSnackbar]);

  return (
    <GenericListingView
      searchFilter={(input: string) => setFilter(input)}
      placeholder={t('data:matrixSearchbarPlaceholder')}
      buttonValue={t('data:createMatrix')}
      onButtonClick={() => createNewData()}
    >
      {loaded && (
      <DataView
        data={dataList}
        filter={filter}
        user={user}
        onDeleteClick={onDeleteClick}
        onUpdateClick={onUpdateClick}
        onMatrixClick={onMatrixClick}
      />
      )}
      {!loaded && (
      <div className={classes.contentloader}>
        <ContentLoader
          speed={2}
          backgroundColor="#dedede"
          foregroundColor="#ececec"
          className={classes.contentloader1}
        >
          <rect x="8%" y="3%" rx="2" ry="2" width="64%" height="6%" />
          <rect x="8%" y="9.4%" rx="2" ry="2" width="64%" height="6%" />
          <rect x="8%" y="15.8%" rx="2" ry="2" width="64%" height="6%" />
          <rect x="8%" y="22.2%" rx="2" ry="2" width="64%" height="6%" />
          <rect x="8%" y="28.6%" rx="2" ry="2" width="64%" height="6%" />
        </ContentLoader>
        <ContentLoader
          speed={2}
          backgroundColor="#B9B9B9"
          foregroundColor="#ececec"
          className={classes.contentloader2}
        >
          <rect x="8%" y="3%" rx="4" ry="4" width=".5%" height="6%" />
          <rect x="8%" y="9.4%" rx="4" ry="4" width=".5%" height="6%" />
          <rect x="8%" y="15.8%" rx="4" ry="4" width=".5%" height="6%" />
          <rect x="8%" y="22.2%" rx="4" ry="4" width=".5%" height="6%" />
          <rect x="8%" y="28.6%" rx="4" ry="4" width=".5%" height="6%" />

          <rect x="9.7%" y="4.5%" rx="4" ry="4" width="5%" height="3%" />
          <rect x="9.7%" y="10.9%" rx="4" ry="4" width="7%" height="3%" />
          <rect x="9.7%" y="17.3%" rx="4" ry="4" width="3%" height="3%" />
          <rect x="9.7%" y="23.7%" rx="4" ry="4" width="10%" height="3%" />
          <rect x="9.7%" y="30.1%" rx="4" ry="4" width="6%" height="3%" />

          <rect x="65.4%" y="4.75%" rx="2" ry="2" width="1.5%" height="2.75%" />
          <rect x="67.6%" y="4.75%" rx="2" ry="2" width="1.5%" height="2.75%" />
          <rect x="69.8%" y="4.75%" rx="2" ry="2" width="1.5%" height="2.75%" />

          <rect x="65.4%" y="11.15%" rx="2" ry="2" width="1.5%" height="2.75%" />
          <rect x="67.6%" y="11.15%" rx="2" ry="2" width="1.5%" height="2.75%" />
          <rect x="69.8%" y="11.15%" rx="2" ry="2" width="1.5%" height="2.75%" />

          <rect x="65.4%" y="17.55%" rx="2" ry="2" width="1.5%" height="2.75%" />
          <rect x="67.6%" y="17.55%" rx="2" ry="2" width="1.5%" height="2.75%" />
          <rect x="69.8%" y="17.55%" rx="2" ry="2" width="1.5%" height="2.75%" />

          <rect x="65.4%" y="23.95%" rx="2" ry="2" width="1.5%" height="2.75%" />
          <rect x="67.6%" y="23.95%" rx="2" ry="2" width="1.5%" height="2.75%" />
          <rect x="69.8%" y="23.95%" rx="2" ry="2" width="1.5%" height="2.75%" />

          <rect x="65.4%" y="30.35%" rx="2" ry="2" width="1.5%" height="2.75%" />
          <rect x="67.6%" y="30.35%" rx="2" ry="2" width="1.5%" height="2.75%" />
          <rect x="69.8%" y="30.35%" rx="2" ry="2" width="1.5%" height="2.75%" />
        </ContentLoader>
      </div>
      )}
      {matrixModal && currentMatrix && (
        <MatrixModal
          open={matrixModal} // Why 'openModal &&' ? => Otherwise previous data are still present
          matrixInfo={currentMatrix}
          onClose={onMatrixModalClose}
        />
      )}
      {openModal && (
        <DataModal
          open={openModal} // Why 'openModal &&' ? => Otherwise previous data are still present
          data={currentData}
          onNewDataUpdate={onNewDataUpdate}
          onClose={onModalClose}
        />
      )}
      {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('data:deleteMatrixConfirmation')}
          handleYes={manageDataDeletion}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </GenericListingView>

  );
};

export default connector(Data);
