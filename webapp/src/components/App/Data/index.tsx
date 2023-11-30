import { useState, useEffect } from "react";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import DeleteIcon from "@mui/icons-material/Delete";
import StorageIcon from "@mui/icons-material/Storage";
import { Box, Typography, IconButton, Tooltip } from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import DownloadIcon from "@mui/icons-material/Download";
import DataPropsView from "./DataPropsView";
import {
  deleteDataSet,
  exportMatrixDataset,
  getMatrixList,
  getExportMatrixUrl,
} from "../../../services/api/matrix";
import { MatrixInfoDTO, MatrixDataSetDTO } from "../../../common/types";
import DatasetCreationDialog from "./DatasetCreationDialog";
import ConfirmationDialog from "../../common/dialogs/ConfirmationDialog";
import RootPage from "../../common/page/RootPage";
import MatrixDialog from "./MatrixDialog";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import SimpleLoader from "../../common/loaders/SimpleLoader";
import SplitLayoutView from "../../common/SplitLayoutView";
import FileTable from "../../common/FileTable";
import { getAuthUser } from "../../../redux/selectors";
import useAppSelector from "../../../redux/hooks/useAppSelector";

function Data() {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const [dataList, setDataList] = useState<Array<MatrixDataSetDTO>>([]);
  const [idForDeletion, setIdForDeletion] = useState<string>();
  const [selectedItem, setSelectedItem] = useState<string>();
  const [loaded, setLoaded] = useState(false);
  const user = useAppSelector(getAuthUser);

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
      enqueueSnackbar(t("data.success.matrixDelete"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("data.error.matrixDelete"), e as AxiosError);
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
          name: tmp.matrices.find((o) => o.id === id)?.name || "",
        });
      }
    }
    setMatrixModal(true);
  };

  const onDownloadDataset = async (datasetId: string) => {
    try {
      await exportMatrixDataset(datasetId);
    } catch (e) {
      enqueueErrorSnackbar(t("data.error.matrix"), e as AxiosError);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const matrix = await getMatrixList();
        setDataList(matrix);
      } catch (e) {
        enqueueErrorSnackbar(t("data.error.matrixList"), e as AxiosError);
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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <RootPage title={t("data.title")} titleIcon={StorageIcon}>
      {loaded && (
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
            <Box sx={{ width: "100%", height: "100%" }}>
              {selectedItem ? (
                <FileTable
                  title={
                    user &&
                    user.id ===
                      dataList.find((item) => item.id === selectedItem)?.owner
                        .id ? (
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}
                      >
                        <Typography
                          sx={{
                            color: "text.primary",
                            fontSize: "1.25rem",
                            fontWeight: 400,
                            lineHeight: 1.334,
                          }}
                        >
                          {`Matrices - ${dataList.find(
                            (item) => item.id === selectedItem,
                          )?.name}`}
                        </Typography>
                        <Box>
                          <IconButton>
                            <Tooltip title={t("global.edit") as string}>
                              <EditIcon
                                onClick={() => {
                                  onUpdateClick(selectedItem);
                                }}
                              />
                            </Tooltip>
                          </IconButton>
                          <IconButton
                            onClick={() => {
                              onDownloadDataset(selectedItem);
                            }}
                          >
                            <Tooltip title={t("global.download") as string}>
                              <DownloadIcon />
                            </Tooltip>
                          </IconButton>
                          <IconButton
                            onClick={() => {
                              handleDelete(selectedItem);
                            }}
                            sx={{
                              color: "error.light",
                            }}
                          >
                            <Tooltip title={t("global.delete") as string}>
                              <DeleteIcon />
                            </Tooltip>
                          </IconButton>
                        </Box>
                      </Box>
                    ) : (
                      <Typography
                        sx={{
                          color: "text.primary",
                          fontSize: "1.25rem",
                          fontWeight: 400,
                          lineHeight: 1.334,
                          height: "40px",
                          display: "flex",
                          alignItems: "center",
                        }}
                      >
                        {`Matrices - ${dataList.find(
                          (item) => item.id === selectedItem,
                        )?.name}`}
                      </Typography>
                    )
                  }
                  content={matrices || []}
                  onDelete={handleDelete}
                  onRead={onMatrixClick}
                  onFileDownload={getExportMatrixUrl}
                  copyId
                />
              ) : (
                <Box />
              )}
            </Box>
          }
        />
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
        <DatasetCreationDialog
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
          {t("data.question.deleteDataset")}
        </ConfirmationDialog>
      )}
    </RootPage>
  );
}

export default Data;
