/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import FileTable from "@/components/FileTable";
import SimpleLoader from "@/components/loaders/SimpleLoader";
import RootPage from "@/components/page/RootPage";
import SplitView from "@/components/page/SplitView";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getAuthUser } from "@/redux/selectors";
import {
  deleteDataSet,
  exportMatrixDataset,
  getExportMatrixUrl,
  getMatrixList,
} from "@/services/api/matrix";
import type { MatrixDataSetDTO, MatrixInfoDTO } from "@/types/types";
import DeleteIcon from "@mui/icons-material/Delete";
import DownloadIcon from "@mui/icons-material/Download";
import EditIcon from "@mui/icons-material/Edit";
import StorageIcon from "@mui/icons-material/Storage";
import { Box, IconButton, Tooltip, Typography } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import type { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import DataPropsView from "./-components/DataPropsView";
import DatasetCreationDialog from "./-components/DatasetCreationDialog";
import MatrixDialog from "./-components/MatrixDialog";

export const Route = createFileRoute("/_authenticated/data/")({
  component: Data,
});

function Data() {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const [dataList, setDataList] = useState<MatrixDataSetDTO[]>([]);
  const [idForDeletion, setIdForDeletion] = useState<string>();
  const [selectedItem, setSelectedItem] = useState<string>();
  const [loaded, setLoaded] = useState(false);
  const user = useAppSelector(getAuthUser);

  // User modal
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [matrixModal, setMatrixModal] = useState<boolean>(false);
  const [currentData, setCurrentData] = useState<MatrixDataSetDTO | undefined>();
  const [currentMatrix, setCurrentMatrix] = useState<MatrixInfoDTO | undefined>();

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
    const tmpList = ([] as MatrixDataSetDTO[]).concat(dataList);
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
        <SplitView splitId="data">
          <DataPropsView
            dataset={dataList}
            onAdd={handleCreation}
            selectedItem={selectedItem || ""}
            setSelectedItem={setSelectedItem}
          />
          <Box sx={{ width: "100%", height: "100%", px: 2 }}>
            {selectedItem ? (
              <FileTable
                title={
                  user &&
                  user.id === dataList.find((item) => item.id === selectedItem)?.owner.id ? (
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
                        {`Matrices - ${dataList.find((item) => item.id === selectedItem)?.name}`}
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
                      {`Matrices - ${dataList.find((item) => item.id === selectedItem)?.name}`}
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
        </SplitView>
      )}
      {!loaded && <SimpleLoader />}
      {matrixModal && currentMatrix && (
        <MatrixDialog matrix={currentMatrix} open={matrixModal} onClose={onMatrixModalClose} />
      )}
      {openModal && (
        <DatasetCreationDialog
          open={openModal}
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
