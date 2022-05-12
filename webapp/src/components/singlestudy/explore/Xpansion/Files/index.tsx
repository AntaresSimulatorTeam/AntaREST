/* eslint-disable react-hooks/exhaustive-deps */
import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { StudyMetadata } from "../../../../../common/types";
import {
  getAllConstraints,
  deleteConstraints,
  getConstraint,
  addConstraints,
} from "../../../../../services/api/xpansion";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import XpansionTable from "../XpansionTable";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import ReaderDialog from "../../../../common/dialogs/ReaderDialog";

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
      enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
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
        enqueueErrorSnackbar(t("xpansion:addFileError"), e as AxiosError);
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
      enqueueErrorSnackbar(t("xpansion:getFileError"), e as AxiosError);
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
        enqueueErrorSnackbar(t("xpansion:deleteFileError"), e as AxiosError);
      }
    }
  };

  useEffect(() => {
    init();
  }, [init]);

  return (
    <>
      {loaded ? (
        <Box width="100%" height="100%" padding={2} boxSizing="border-box">
          <XpansionTable
            title={t("main:files")}
            content={constraints || []}
            onDelete={deleteConstraint}
            onRead={getOneConstraint}
            uploadFile={addOneConstraint}
          />
        </Box>
      ) : (
        <SimpleLoader />
      )}
      {!!constraintViewDialog && (
        <ReaderDialog
          data={constraintViewDialog}
          onClose={() => setConstraintViewDialog(undefined)}
        />
      )}
    </>
  );
}

export default Files;
