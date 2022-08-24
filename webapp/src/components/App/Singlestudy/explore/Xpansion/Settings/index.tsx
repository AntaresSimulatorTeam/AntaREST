import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box, Paper } from "@mui/material";
import { useSnackbar } from "notistack";
import { StudyMetadata } from "../../../../../../common/types";
import { XpansionSettings } from "../types";
import {
  getXpansionSettings,
  getAllConstraints,
  getConstraint,
  updateXpansionSettings,
} from "../../../../../../services/api/xpansion";
import SettingsForm from "./SettingsForm";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import { removeEmptyFields } from "../../../../../../services/utils/index";
import DataViewerDialog from "../../../../../common/dialogs/DataViewerDialog";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";

function Settings() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [constraintViewDialog, setConstraintViewDialog] = useState<{
    filename: string;
    content: string;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const {
    data: settings,
    isLoading: settingsLoading,
    reload: reloadSettings,
  } = usePromiseWithSnackbarError(
    async () => {
      if (study) {
        return getXpansionSettings(study.id);
      }
    },
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
    }
  );

  const { data: constraints, isLoading: constraintsLoading } =
    usePromiseWithSnackbarError(
      async () => {
        if (study) {
          return getAllConstraints(study.id);
        }
      },
      {
        errorMessage: t("xpansion.error.loadConfiguration"),
      }
    );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const updateSettings = async (value: XpansionSettings) => {
    try {
      if (study) {
        await updateXpansionSettings(
          study.id,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          removeEmptyFields(value as { [key: string]: any }, [
            "cut-type",
            "solver",
            "yearly-weights",
            "additional-constraints",
          ]) as XpansionSettings
        );
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.updateSettings"), e as AxiosError);
    } finally {
      reloadSettings();
      enqueueSnackbar(t("studies.success.saveData"), {
        variant: "success",
      });
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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {!settingsLoading && !constraintsLoading && settings ? (
        <Box sx={{ width: "100%", height: "100%", p: 2 }}>
          <Paper sx={{ width: "100%", height: "100%", p: 2 }}>
            <SettingsForm
              settings={settings}
              constraints={constraints || []}
              updateSettings={updateSettings}
              onRead={getOneConstraint}
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

export default Settings;
