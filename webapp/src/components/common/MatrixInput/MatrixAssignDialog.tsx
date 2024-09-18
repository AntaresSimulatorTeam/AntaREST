/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { Box, Button, Divider, Typography } from "@mui/material";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { MatrixInfoDTO, StudyMetadata } from "../../../common/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import { getMatrix, getMatrixList } from "../../../services/api/matrix";
import { appendCommands } from "../../../services/api/variant";
import DataPropsView from "../../App/Data/DataPropsView";
import { CommandEnum } from "../../App/Singlestudy/Commands/Edition/commandTypes";
import ButtonBack from "../ButtonBack";
import BasicDialog, { BasicDialogProps } from "../dialogs/BasicDialog";
import EditableMatrix from "../EditableMatrix";
import FileTable from "../FileTable";
import UsePromiseCond from "../utils/UsePromiseCond";
import SplitView from "../SplitView";

interface Props {
  study: StudyMetadata;
  path: string;
  open: BasicDialogProps["open"];
  onClose: VoidFunction;
}

function MatrixAssignDialog(props: Props) {
  const [t] = useTranslation();
  const { study, path, open, onClose } = props;
  const [selectedItem, setSelectedItem] = useState("");
  const [currentMatrix, setCurrentMatrix] = useState<MatrixInfoDTO>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const resList = usePromiseWithSnackbarError(() => getMatrixList(), {
    errorMessage: t("data.error.matrixList"),
  });

  const resMatrix = usePromiseWithSnackbarError(
    async () => {
      if (currentMatrix) {
        const res = await getMatrix(currentMatrix.id);
        return res;
      }
    },
    {
      errorMessage: t("data.error.matrix"),
      deps: [currentMatrix],
    },
  );

  useEffect(() => {
    setCurrentMatrix(undefined);
  }, [selectedItem]);

  const dataSet = resList.data?.find((item) => item.id === selectedItem);
  const matrices = dataSet?.matrices;
  const matrixName = `${t("global.matrices")} - ${dataSet?.name}`;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleMatrixClick = async (id: string) => {
    if (matrices) {
      setCurrentMatrix({
        id,
        name: matrices.find((o) => o.id === id)?.name || "",
      });
    }
  };

  const handleAssignation = async (matrixId: string) => {
    try {
      await appendCommands(study.id, [
        {
          action: CommandEnum.REPLACE_MATRIX,
          args: {
            target: path,
            matrix: matrixId,
          },
        },
      ]);
      enqueueSnackbar(t("data.success.matrixAssignation"), {
        variant: "success",
      });
      onClose();
    } catch (e) {
      enqueueErrorSnackbar(t("data.error.matrixAssignation"), e as AxiosError);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      open={open}
      onClose={onClose}
      title={t("data.assignMatrix")}
      sx={{
        "& .MuiDialog-paper": { maxWidth: "unset" },
      }}
      actions={<Button onClick={onClose}>{t("global.close")}</Button>}
      contentProps={{
        sx: { width: "1200px", height: "700px" },
      }}
    >
      <UsePromiseCond
        response={resList}
        ifResolved={(dataset) =>
          dataset && (
            <SplitView id="matrix-assign" sizes={[20, 80]}>
              <DataPropsView
                dataset={dataset}
                selectedItem={selectedItem}
                setSelectedItem={setSelectedItem}
              />
              <Box sx={{ width: 1, height: 1, px: 2 }}>
                {selectedItem && !currentMatrix && (
                  <FileTable
                    title={
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
                          {matrixName}
                        </Typography>
                      </Box>
                    }
                    content={matrices || []}
                    onRead={handleMatrixClick}
                    onAssign={handleAssignation}
                  />
                )}
                <UsePromiseCond
                  response={resMatrix}
                  ifResolved={(matrix) =>
                    matrix && (
                      <>
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
                            {matrixName}
                          </Typography>

                          <Box display="flex" justifyContent="flex-end">
                            <ButtonBack
                              onClick={() => setCurrentMatrix(undefined)}
                            />
                          </Box>
                        </Box>
                        <Divider sx={{ mt: 1, mb: 2 }} />
                        <EditableMatrix
                          matrix={matrix}
                          readOnly
                          matrixTime={false}
                        />
                      </>
                    )
                  }
                />
              </Box>
            </SplitView>
          )
        }
      />
    </BasicDialog>
  );
}

export default MatrixAssignDialog;
