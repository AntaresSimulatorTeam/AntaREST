/* eslint-disable react-hooks/exhaustive-deps */
import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { MatrixType, StudyMetadata } from "../../../../../common/types";
import {
  getAllCapacities,
  deleteCapacity,
  getCapacity,
  addCapacity,
} from "../../../../../services/api/xpansion";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import MatrixView from "../../../../common/MatrixView";
import BasicModal from "../../../../common/BasicModal";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import XpansionTable from "../XpansionTable";

function Capacities() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [capacities, setCapacities] = useState<Array<string>>();
  const [loaded, setLoaded] = useState<boolean>(false);
  const [capacityViewModal, setCapacityViewModal] = useState<{
    filename: string;
    content: MatrixType;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const init = useCallback(async () => {
    try {
      if (study) {
        const tempCapa = await getAllCapacities(study.id);
        setCapacities(tempCapa);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
    } finally {
      setLoaded(true);
    }
  }, [study?.id, t]);

  const addOneCapa = async (file: File) => {
    if (capacities) {
      try {
        if (study) {
          await addCapacity(study.id, file);
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:addFileError"), e as AxiosError);
      } finally {
        init();
      }
    }
  };

  const getOneCapa = async (filename: string) => {
    try {
      if (study) {
        const content = await getCapacity(study.id, filename);
        setCapacityViewModal({ filename, content });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:getFileError"), e as AxiosError);
    }
  };

  const deleteCapa = async (filename: string) => {
    if (capacities) {
      const tempCapa = capacities.filter((a) => a !== filename);
      try {
        if (study) {
          await deleteCapacity(study.id, filename);
          setCapacities(tempCapa);
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
            title={t("xpansion:capacities")}
            content={capacities || []}
            onDelete={deleteCapa}
            onRead={getOneCapa}
            uploadFile={addOneCapa}
          />
        </Box>
      ) : (
        <SimpleLoader />
      )}
      {!!capacityViewModal && (
        <BasicModal
          open={!!capacityViewModal}
          title={capacityViewModal.filename}
          onClose={() => setCapacityViewModal(undefined)}
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
            height="600px"
            display="flex"
            flexDirection="column"
            alignItems="flex-start"
            overflow="auto"
            padding="8px"
          >
            <MatrixView matrix={capacityViewModal.content} readOnly />
          </Box>
        </BasicModal>
      )}
    </>
  );
}

export default Capacities;
