import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box, Paper } from "@mui/material";
import { StudyMetadata } from "../../../../../../common/types";
import {
  getAllConstraints,
  deleteConstraints,
  getConstraint,
  addConstraints,
} from "../../../../../../services/api/xpansion";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import FileTable from "../../../../../common/FileTable";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import DataViewerDialog from "../../../../../common/dialogs/DataViewerDialog";
import { Title } from "../share/styles";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";

function Files() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [constraintViewDialog, setConstraintViewDialog] = useState<{
    filename: string;
    content: string;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const res = usePromiseWithSnackbarError(
    async () => {
      if (study) {
        return getAllConstraints(study.id);
      }
    },
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
    }
  );

  const { data: constraints, reload: reloadConstraints } = res;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const addOneConstraint = async (file: File) => {
    if (constraints) {
      try {
        if (study) {
          await addConstraints(study.id, file);
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion.error.addFile"), e as AxiosError);
      } finally {
        reloadConstraints();
      }
    }
  };

  const getOneConstraint = async (filename: string) => {
    try {
      if (study) {
        const content = await getConstraint(study.id, filename);
        setConstraintViewDialog({ filename, content });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.getFile"), e as AxiosError);
    }
  };

  const deleteConstraint = async (filename: string) => {
    try {
      if (study) {
        await deleteConstraints(study.id, filename);
        reloadConstraints();
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
                title={<Title>{t("global.files")}</Title>}
                content={data?.map((item) => ({ id: item, name: item })) || []}
                onDelete={deleteConstraint}
                onRead={getOneConstraint}
                uploadFile={addOneConstraint}
                allowImport
                allowDelete
              />
            </Paper>
          </Box>
        )}
      />
      {!!constraintViewDialog && (
        <DataViewerDialog
          studyId={study?.id || ""}
          filename={constraintViewDialog.filename}
          content={constraintViewDialog.content}
          onClose={() => setConstraintViewDialog(undefined)}
        />
      )}
    </>
  );
}

export default Files;
