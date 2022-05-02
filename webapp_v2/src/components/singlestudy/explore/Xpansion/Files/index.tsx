/* eslint-disable react-hooks/exhaustive-deps */
import { useCallback, useEffect, useState } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { StudyMetadata } from "../../../../../common/types";
import {
  xpansionConfigurationExist,
  getAllConstraints,
  deleteConstraints,
  getConstraint,
  addConstraints,
} from "../../../../../services/api/xpansion";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import BasicModal from "../../../../common/BasicModal";
import XpansionTable from "../XpansionTable";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";

function Files() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const navigate = useNavigate();
  const [constraints, setConstraints] = useState<Array<string>>();
  const [loaded, setLoaded] = useState<boolean>(false);
  const [constraintViewModal, setConstraintViewModal] = useState<{
    filename: string;
    content: string;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const init = useCallback(async () => {
    try {
      if (study) {
        const exist = await xpansionConfigurationExist(study.id);
        if (exist) {
          if (study) {
            const tempConstraints = await getAllConstraints(study.id);
            setConstraints(tempConstraints);
          }
        } else {
          navigate("Filesandidates");
        }
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
        setConstraintViewModal({ filename, content });
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
      {!!constraintViewModal && (
        <BasicModal
          open={!!constraintViewModal}
          title={constraintViewModal.filename}
          onClose={() => setConstraintViewModal(undefined)}
          rootStyle={{
            backgroundColor: "white",
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
            <code style={{ whiteSpace: "pre" }}>
              {constraintViewModal.content}
            </code>
          </Box>
        </BasicModal>
      )}
    </>
  );
}

export default Files;
