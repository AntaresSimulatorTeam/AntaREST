/* eslint-disable react-hooks/exhaustive-deps */
import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { useSnackbar } from "notistack";
import { StudyMetadata } from "../../../../../common/types";
import { XpansionSettings } from "../types";
import {
  getXpansionSettings,
  getAllConstraints,
  getConstraint,
  updateXpansionSettings,
} from "../../../../../services/api/xpansion";
import SettingsForm from "./SettingsForm";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import { removeEmptyFields } from "../../../../../services/utils/index";
import DataViewerDialog from "../../../../common/dialogs/DataViewerDialog";

function Settings() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [settings, setSettings] = useState<XpansionSettings>();
  const [constraints, setConstraints] = useState<Array<string>>();
  const [loaded, setLoaded] = useState<boolean>(false);
  const [constraintViewDialog, setConstraintViewDialog] = useState<{
    filename: string;
    content: string;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const initSettings = useCallback(async () => {
    try {
      if (study) {
        const tempSettings = await getXpansionSettings(study.id);
        setSettings(tempSettings);
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t("global:xpansion.error.loadConfiguration"),
        e as AxiosError
      );
    }
  }, [study?.id, t]);

  const initFiles = useCallback(async () => {
    try {
      if (study) {
        const tempConstraints = await getAllConstraints(study.id);
        setConstraints(tempConstraints);
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t("global:xpansion.error.loadConfiguration"),
        e as AxiosError
      );
    }
  }, [study?.id, t]);

  const init = useCallback(async () => {
    try {
      if (study) {
        initSettings();
        initFiles();
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t("global:xpansion.error.loadConfiguration"),
        e as AxiosError
      );
    } finally {
      setLoaded(true);
    }
  }, [study?.id, t, initSettings, initFiles]);

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
      enqueueErrorSnackbar(
        t("global:xpansion.error.updateSettings"),
        e as AxiosError
      );
    } finally {
      initSettings();
      enqueueSnackbar(t("global:studies.success.saveData"), {
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
      enqueueErrorSnackbar(t("global:xpansion.error.getFile"), e as AxiosError);
    }
  };

  useEffect(() => {
    init();
  }, [init]);

  return (
    <>
      {loaded && settings ? (
        <Box width="100%" height="100%" padding={2} boxSizing="border-box">
          <SettingsForm
            settings={settings}
            constraints={constraints || []}
            updateSettings={updateSettings}
            onRead={getOneConstraint}
          />
        </Box>
      ) : (
        <SimpleLoader />
      )}
      {!!constraintViewDialog && (
        <DataViewerDialog
          data={constraintViewDialog}
          onClose={() => setConstraintViewDialog(undefined)}
        />
      )}
    </>
  );
}

export default Settings;
