/* eslint-disable react-hooks/exhaustive-deps */
import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box, Paper } from "@mui/material";
import { StudyMetadata } from "../../../../../common/types";
import {
  getAllConstraints,
  deleteConstraints,
  getConstraint,
  addConstraints,
} from "../../../../../services/api/xpansion";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import FileTable from "../../../../common/FileTable";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import DataViewerDialog from "../../../../common/dialogs/DataViewerDialog";
import { Title } from "../share/styles";

function Files() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [constraints, setConstraints] = useState<Array<string>>();
  const [loaded, setLoaded] = useState<boolean>(false);
  const [constraintViewDialog, setConstraintViewDialog] = useState<{
    filename: string;
    content: string;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const init = useCallback(async () => {
    try {
      if (study) {
        const tempConstraints = await getAllConstraints(study.id);
        setConstraints(tempConstraints);
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t("xpansion.error.loadConfiguration"),
        e as AxiosError
      );
    } finally {
      setLoaded(true);
    }
  }, [study?.id, t]);

  const addOneConstraint = async (file: File) => {
    if (constraints) {
      try {
        if (study) {
          await addConstraints(study.id, file);
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion.error.addFile"), e as AxiosError);
      } finally {
        init();
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
    if (constraints) {
      const tempConstraints = constraints.filter((a) => a !== filename);
      try {
        if (study) {
          await deleteConstraints(study.id, filename);
          setConstraints(tempConstraints);
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion.error.deleteFile"), e as AxiosError);
      }
    }
  };

  useEffect(() => {
    init();
  }, [init]);

  return (
    <>
      {loaded ? (
        <Box sx={{ width: "100%", height: "100%", p: 2 }}>
          <Paper sx={{ width: "100%", height: "100%", p: 2 }}>
            <FileTable
              title={<Title>{t("global.files")}</Title>}
              content={
                constraints?.map((item) => ({ id: item, name: item })) || []
              }
              onDelete={deleteConstraint}
              onRead={getOneConstraint}
              uploadFile={addOneConstraint}
              allowImport
              allowDelete
            />
          </Paper>
        </Box>
      ) : (
        <SimpleLoader />
      )}
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
