/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useMemo, useState } from "react";
import { AxiosError } from "axios";
import { useOutletContext } from "react-router-dom";
import { Box, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../common/types";
import {
  createXpansionConfiguration,
  xpansionConfigurationExist,
} from "../../../../../services/api/xpansion";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import TabWrapper from "../TabWrapper";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";

function Xpansion() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [exist, setExist] = useState<boolean>(false);

  const { data: configExist } = usePromiseWithSnackbarError(
    () => xpansionConfigurationExist(study.id),
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
      deps: [exist],
    }
  );

  const tabList = useMemo(
    () => [
      {
        label: t("xpansion.candidates"),
        path: `/studies/${study?.id}/explore/xpansion/candidates`,
      },
      {
        label: t("global.settings"),
        path: `/studies/${study?.id}/explore/xpansion/settings`,
      },
      {
        label: t("global.files"),
        path: `/studies/${study?.id}/explore/xpansion/files`,
      },
      {
        label: t("xpansion.capacities"),
        path: `/studies/${study?.id}/explore/xpansion/capacities`,
      },
    ],
    [study]
  );

  useEffect(() => {
    if (window.history.state.usr !== null) {
      setExist(window.history.state.usr.exist);
    }
  }, [window.history.state.usr]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const createXpansion = async () => {
    try {
      if (study) {
        await createXpansionConfiguration(study.id);
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t("xpansion.error.createConfiguration"),
        e as AxiosError
      );
    } finally {
      setExist(true);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      width="100%"
      flexGrow={1}
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      boxSizing="border-box"
      overflow="hidden"
    >
      {!configExist && !exist ? (
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          width="100%"
          flexGrow={1}
        >
          <Button
            sx={{
              width: "140px",
            }}
            variant="contained"
            onClick={createXpansion}
          >
            {t("xpansion.newXpansionConfig")}
          </Button>
        </Box>
      ) : (
        <TabWrapper study={study} tabStyle="withoutBorder" tabList={tabList} />
      )}
    </Box>
  );
}

export default Xpansion;
