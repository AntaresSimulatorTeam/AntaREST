import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box, Paper } from "@mui/material";
import { useSnackbar } from "notistack";
import { StudyMetadata } from "../../../../../../common/types";
import { XpansionResourceType, XpansionSettings } from "../types";
import {
  getXpansionSettings,
  getAllConstraints,
  getConstraint,
  updateXpansionSettings,
  getAllWeights,
  getWeight,
} from "../../../../../../services/api/xpansion";
import SettingsForm from "./SettingsForm";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import { removeEmptyFields } from "../../../../../../services/utils/index";
import DataViewerDialog from "../../../../../common/dialogs/DataViewerDialog";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";

const resourceContentFetcher = (
  resourceType: string
): ((uuid: string, filename: string) => Promise<string>) => {
  if (resourceType === XpansionResourceType.constraints) {
    return getConstraint;
  }
  return getWeight;
};

function Settings() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [resourceViewDialog, setResourceViewDialog] = useState<{
    filename: string;
    content: string;
    isMatrix: boolean;
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

  const { data: constraints } = usePromiseWithSnackbarError(
    async () => {
      if (study) {
        return getAllConstraints(study.id);
      }
    },
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
    }
  );

  const { data: weights } = usePromiseWithSnackbarError(
    async () => {
      if (study) {
        return getAllWeights(study.id);
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

  const getResourceContent = async (resourceType: string, filename: string) => {
    try {
      if (study) {
        const content = await resourceContentFetcher(resourceType)(
          study.id,
          filename
        );
        setResourceViewDialog({
          filename,
          content,
          isMatrix: resourceType === XpansionResourceType.weights,
        });
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
      {!settingsLoading && settings ? (
        <Box sx={{ width: "100%", flexGrow: 1, overflow: "hidden", p: 2 }}>
          <Paper sx={{ width: "100%", height: "100%", overflow: "auto", p: 2 }}>
            <SettingsForm
              settings={settings}
              constraints={constraints || []}
              weights={weights || []}
              updateSettings={updateSettings}
              onRead={getResourceContent}
            />
          </Paper>
        </Box>
      ) : (
        <SimpleLoader />
      )}
      {!!resourceViewDialog && (
        <DataViewerDialog
          studyId={study?.id || ""}
          filename={resourceViewDialog.filename}
          content={resourceViewDialog.content}
          onClose={() => setResourceViewDialog(undefined)}
          isMatrix={resourceViewDialog.isMatrix}
        />
      )}
    </>
  );
}

export default Settings;
