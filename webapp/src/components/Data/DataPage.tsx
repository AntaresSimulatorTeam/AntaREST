import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { AxiosError } from 'axios';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../App/reducers';
import GenericListingView from '../ui/NavComponents/GenericListingView';
import DataView from './DataView';
import DataViewLoader from './DataViewLoader';
import { deleteDataSet, getMatrixList } from '../../services/api/matrix';
import { MatrixDataSetDTO, IDType, MatrixInfoDTO } from '../../common/types';
import DataModal from './DataModal';
import ConfirmationModal from '../ui/ConfirmationModal';
import MatrixModal from './MatrixModal';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import NoContent from '../ui/NoContent';

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const Data = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
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
      {loaded && dataList.length > 0 ? (
        <DataView
          data={dataList}
          filter={filter}
          user={user}
          onDeleteClick={onDeleteClick}
          onUpdateClick={onUpdateClick}
          onMatrixClick={onMatrixClick}
        />
      ) : loaded && (
        <div style={{ height: '90%' }}>
          <NoContent />
        </div>
      )}
      {!loaded && <DataViewLoader />}
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
