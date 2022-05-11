import { useState, useEffect } from "react";
import { connect, ConnectedProps } from "react-redux";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import DeleteIcon from "@mui/icons-material/Delete";
import StorageIcon from "@mui/icons-material/Storage";
import { Box } from "@mui/material";
import { AppState } from "../store/reducers";
import DataPropsView from "../components/data/DataPropsView";
import {
  deleteDataSet,
  exportMatrixDataset,
  getMatrixList,
} from "../services/api/matrix";
import { MatrixInfoDTO, MatrixDataSetDTO } from "../common/types";
import DataDialog from "../components/data/DataDialog";
import ConfirmationDialog from "../components/common/dialogs/ConfirmationDialog";
import RootPage from "../components/common/page/RootPage";
import MatrixDialog from "../components/data/MatrixDialog";
import useEnqueueErrorSnackbar from "../hooks/useEnqueueErrorSnackbar";
import NoContent from "../components/common/page/NoContent";
import SimpleLoader from "../components/common/loaders/SimpleLoader";
import SplitLayoutView from "../components/common/SplitLayoutView";
import FileTable from "../components/common/FileTable";

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

function Data(props: PropTypes) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const [dataList, setDataList] = useState<Array<MatrixDataSetDTO>>([]);
  const [idForDeletion, setIdForDeletion] = useState<string>();
  const [selectedItem, setSelectedItem] = useState<string>();
  const { user } = props;
  const [loaded, setLoaded] = useState(false);

  // User modal
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<boolean>(false);
  const [matrixModal, setMatrixModal] = useState<boolean>(false);
  const [currentData, setCurrentData] = useState<
    MatrixDataSetDTO | undefined
  >();
  const [currentMatrix, setCurrentMatrix] = useState<
    MatrixInfoDTO | undefined
  >();

  const handleCreation = () => {
    setCurrentData(undefined);
    setOpenModal(true);
  };

  const onUpdateClick = (id: string): void => {
    setCurrentData(dataList.find((item) => item.id === id));
    setOpenModal(true);
  };

  const handleDelete = async (id: string) => {
    setIdForDeletion(id);
    setOpenConfirmationModal(true);
  };

  const manageDataDeletion = async () => {
    try {
      await deleteDataSet(idForDeletion as string);
      setDataList(dataList.filter((item) => item.id !== idForDeletion));
      enqueueSnackbar(t("data:onMatrixDeleteSuccess"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("data:onMatrixDeleteError"), e as AxiosError);
    }
    setIdForDeletion(undefined);
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

  const onMatrixClick = async (id: string) => {
    if (selectedItem) {
      const tmp = dataList.find((o) => o.id === selectedItem);
      if (tmp) {
        setCurrentMatrix({
          id,
          name: tmp.matrices.find((o) => o.id === id)?.id || "",
        });
      }
    }
    setMatrixModal(true);
  };

  const onDownloadDataset = async (datasetId: string) => {
    try {
      await exportMatrixDataset(datasetId);
    } catch (e) {
      enqueueErrorSnackbar(t("data:matrixError"), e as AxiosError);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const matrix = await getMatrixList();
        setDataList(matrix);
      } catch (e) {
        enqueueErrorSnackbar(t("data:matrixListError"), e as AxiosError);
      } finally {
        setLoaded(true);
      }
    };
    init();
    return () => {
      setDataList([]);
    };
  }, [user, t, enqueueErrorSnackbar]);

  const matrices = dataList.find((item) => item.id === selectedItem)?.matrices;

  return (
    <RootPage title={t("main:data")} titleIcon={StorageIcon}>
      {loaded && dataList.length > 0 ? (
        <SplitLayoutView
          left={
            <DataPropsView
              dataset={dataList}
              onAdd={handleCreation}
              selectedItem={selectedItem || ""}
              setSelectedItem={setSelectedItem}
            />
          }
          right={
            <Box sx={{ width: "100%" }}>
              <FileTable
                title="Matrices"
                content={matrices || []}
                onDelete={handleDelete}
                onRead={onMatrixClick}
              />
            </Box>
          }
        />
      ) : (
        loaded && <NoContent />
      )}
      {!loaded && <SimpleLoader />}
      {matrixModal && currentMatrix && (
        <MatrixDialog
          open={matrixModal} // Why 'openModal &&' ? => Otherwise previous data are still present
          matrixInfo={currentMatrix}
          onClose={onMatrixModalClose}
        />
      )}
      {openModal && (
        <DataDialog
          open={openModal} // Why 'openModal &&' ? => Otherwise previous data are still present
          data={currentData}
          onNewDataUpdate={onNewDataUpdate}
          onClose={onModalClose}
        />
      )}
      {openConfirmationModal && (
        <ConfirmationDialog
          open
          titleIcon={DeleteIcon}
          onConfirm={() => {
            manageDataDeletion();
            setOpenConfirmationModal(false);
          }}
          onCancel={() => setOpenConfirmationModal(false)}
          alert="warning"
        >
          {t("data:deleteMatrixConfirmation")}
        </ConfirmationDialog>
      )}
    </RootPage>
  );
}

export default connector(Data);
