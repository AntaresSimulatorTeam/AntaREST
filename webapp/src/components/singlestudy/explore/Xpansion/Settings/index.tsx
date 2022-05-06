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
import BasicModal from "../../../../common/BasicModal";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import { removeEmptyFields } from "../../../../../services/utils/index";

function Settings() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [settings, setSettings] = useState<XpansionSettings>();
  const [constraints, setConstraints] = useState<Array<string>>();
  const [loaded, setLoaded] = useState<boolean>(false);
  const [constraintViewModal, setConstraintViewModal] = useState<{
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
      enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
    }
  }, [study?.id, t]);

  const initFiles = useCallback(async () => {
    try {
      if (study) {
        const tempConstraints = await getAllConstraints(study.id);
        setConstraints(tempConstraints);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
    }
  }, [study?.id, t]);

  const init = useCallback(async () => {
    try {
      if (study) {
        initSettings();
        initFiles();
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
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
      enqueueErrorSnackbar(t("xpansion:updateSettingsError"), e as AxiosError);
    } finally {
      initSettings();
      enqueueSnackbar(t("studymanager:savedatasuccess"), {
        variant: "success",
      });
    }
  };

  const getOneConstraint = async (filename: string) => {
    try {
      if (study) {
        const content = await getConstraint(study.id, filename);
        setConstraintViewModal({ filename, content });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:getFileError"), e as AxiosError);
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
      {!!constraintViewModal && (
        <BasicModal
          open={!!constraintViewModal}
          title={constraintViewModal.filename}
          onClose={() => setConstraintViewModal(undefined)}
          rootStyle={{
            maxWidth: "80%",
            maxHeight: "70%",
            display: "flex",
            flexFlow: "column nowrap",
            alignItems: "center",
          }}
        >
          <Box
            width="900px"
            height="500px"
            display="flex"
            flexDirection="column"
            alignItems="flex-start"
            padding="8px"
          >
            <code style={{ whiteSpace: "pre" }}>
              {constraintViewModal.content}
            </code>
          </Box>
        </BasicModal>
      )}
    </>
  );
}

export default Settings;
