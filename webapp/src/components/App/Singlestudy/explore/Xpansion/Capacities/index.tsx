import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box, Paper } from "@mui/material";
import { MatrixType, StudyMetadata } from "../../../../../../common/types";
import {
  getAllCapacities,
  deleteCapacity,
  getCapacity,
  addCapacity,
} from "../../../../../../services/api/xpansion";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import DataViewerDialog from "../../../../../common/dialogs/DataViewerDialog";
import FileTable from "../../../../../common/FileTable";
import { Title } from "../share/styles";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";

function Capacities() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [capacityViewDialog, setCapacityViewDialog] = useState<{
    filename: string;
    content: MatrixType;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const res = usePromiseWithSnackbarError(
    async () => {
      if (study) {
        return getAllCapacities(study.id);
      }
    },
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
    }
  );

  const { data: capacities, reload: reloadCapacities } = res;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const addOneCapa = async (file: File) => {
    if (capacities) {
      try {
        if (study) {
          await addCapacity(study.id, file);
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion.error.addFile"), e as AxiosError);
      } finally {
        reloadCapacities();
      }
    }
  };

  const getOneCapa = async (filename: string) => {
    try {
      if (study) {
        const content = await getCapacity(study.id, filename);
        setCapacityViewDialog({ filename, content });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.getFile"), e as AxiosError);
    }
  };

  const deleteCapa = async (filename: string) => {
    try {
      if (study) {
        await deleteCapacity(study.id, filename);
        reloadCapacities();
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.deleteFile"), e as AxiosError);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <UsePromiseCond
        response={res}
        ifPending={() => <SimpleLoader />}
        ifRejected={(error) => <div>{error?.toString()}</div>}
        ifResolved={(data) => (
          <Box sx={{ width: "100%", height: "100%", p: 2 }}>
            <Paper sx={{ width: "100%", height: "100%", p: 2 }}>
              <FileTable
                title={<Title>{t("xpansion.capacities")}</Title>}
                content={data?.map((item) => ({ id: item, name: item })) || []}
                onDelete={deleteCapa}
                onRead={getOneCapa}
                uploadFile={addOneCapa}
                allowImport
                allowDelete
              />
            </Paper>
          </Box>
        )}
      />
      {!!capacityViewDialog && (
        <DataViewerDialog
          studyId={study?.id || ""}
          filename={capacityViewDialog.filename}
          content={capacityViewDialog.content}
          onClose={() => setCapacityViewDialog(undefined)}
          isMatrix
        />
      )}
    </>
  );
}

export default Capacities;
