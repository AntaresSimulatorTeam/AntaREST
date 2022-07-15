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
import SimpleLoader from "../loaders/SimpleLoader";
import SplitLayoutView from "../SplitLayoutView";
import UsePromiseCond from "../utils/UsePromiseCond";

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
    }
  );

  useEffect(() => {
    setCurrentMatrix(undefined);
  }, [selectedItem]);

  const dataSet = resList.data?.find((item) => item.id === selectedItem);
  const matrices = dataSet?.matrices;
  const matrixName = `${t("global.matrixes")} - ${dataSet?.name}`;

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
      enqueueSnackbar(t("data.succes.matrixAssignation"), {
        variant: "success",
      });
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
      actions={<Button onClick={onClose}>{t("button.close")}</Button>}
      contentProps={{
        sx: { width: "1200px", height: "700px" },
      }}
    >
      <UsePromiseCond
        response={resList}
        ifPending={() => <SimpleLoader />}
        ifRejected={(error) => <div>{error}</div>}
        ifResolved={(dataset) =>
          dataset && (
            <SplitLayoutView
              left={
                <DataPropsView
                  dataset={dataset}
                  selectedItem={selectedItem}
                  setSelectedItem={setSelectedItem}
                />
              }
              right={
                <Box sx={{ width: "100%", height: "100%" }}>
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
                    ifPending={() => <SimpleLoader />}
                    ifRejected={(error) => <div>{error}</div>}
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
                            toggleView
                          />
                        </>
                      )
                    }
                  />
                </Box>
              }
            />
          )
        }
      />
    </BasicDialog>
  );
}

export default MatrixAssignDialog;
