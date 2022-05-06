/* eslint-disable react-hooks/exhaustive-deps */
import { useMemo, useEffect, useState } from "react";
import { AxiosError } from "axios";
import { useOutletContext } from "react-router-dom";
import { Box, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../common/types";
import {
  createXpansionConfiguration,
  xpansionConfigurationExist,
} from "../../../../services/api/xpansion";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import TabWrapper from "../TabWrapper";

function Xpansion() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [configExist, setConfigExist] = useState<boolean>(true);

  const tabList = useMemo(
    () => [
      {
        label: t("xpansion:candidates"),
        path: `/studies/${study?.id}/explore/xpansion/candidates`,
      },
      {
        label: t("main:settings"),
        path: `/studies/${study?.id}/explore/xpansion/settings`,
      },
      {
        label: t("main:files"),
        path: `/studies/${study?.id}/explore/xpansion/files`,
      },
      {
        label: t("xpansion:capacities"),
        path: `/studies/${study?.id}/explore/xpansion/capacities`,
      },
    ],
    [study]
  );

  const createXpansion = async () => {
    try {
      if (study) {
        await createXpansionConfiguration(study.id);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:createXpansionError"), e as AxiosError);
    } finally {
      setConfigExist(true);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        if (study) {
          const exist = await xpansionConfigurationExist(study.id);
          setConfigExist(exist);
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
      }
    };
    init();
  });

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
      {!configExist ? (
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
            {t("xpansion:newXpansionConfig")}
          </Button>
        </Box>
      ) : (
        <TabWrapper study={study} tabStyle="withoutBorder" tabList={tabList} />
      )}
    </Box>
  );
}

export default Xpansion;
