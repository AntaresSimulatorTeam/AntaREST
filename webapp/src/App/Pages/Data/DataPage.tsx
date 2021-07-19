import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../reducers';
import GenericSettingView from '../../../components/Settings/GenericSettingView';
import DataView from '../../../components/Data/DataView';
import { deleteDataSet, getMatrixList } from '../../../services/api/matrix';
import { MatrixDataSetDTO, IDType, MatrixInfoDTO } from '../../../common/types';
import DataModal from './DataModal';
import ConfirmationModal from '../../../components/ui/ConfirmationModal';
import MatrixModal from './MatrixModal';

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
      enqueueSnackbar(t('data:onMatrixDeleteError'), { variant: 'error' });
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
    console.log(matrixInfo);
  };

  useEffect(() => {
    const init = async () => {
      try {
        const matrix = await getMatrixList();
        setDataList(matrix);
      } catch (e) {
        enqueueSnackbar(t('data:matrixError'), { variant: 'error' });
      }
    };
    init();
    return () => {
      setDataList([]);
    };
  }, [user, t, enqueueSnackbar]);

  return (
    <GenericSettingView
      searchFilter={(input: string) => setFilter(input)}
      placeholder={t('data:matrixSearchbarPlaceholder')}
      buttonValue={t('data:createMatrix')}
      onButtonClick={() => createNewData()}
    >

      <DataView
        data={dataList}
        filter={filter}
        user={user}
        onDeleteClick={onDeleteClick}
        onUpdateClick={onUpdateClick}
        onMatrixClick={onMatrixClick}
      />
      {matrixModal && (
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
    </GenericSettingView>

  );
};

export default connector(Data);
