/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Backdrop, Box, CircularProgress } from "@mui/material";
import { usePromise as usePromiseWrapper } from "react-use";
import { useSnackbar } from "notistack";
import { MatrixType, StudyMetadata } from "../../../../../common/types";
import { XpansionCandidate } from "../types";
import SplitLayoutView from "../../../../common/SplitLayoutView";
import {
  getAllCandidates,
  getAllCapacities,
  deleteXpansionConfiguration,
  addCandidate,
  deleteCandidate,
  updateCandidate,
  getCapacity,
} from "../../../../../services/api/xpansion";
import {
  transformNameToId,
  removeEmptyFields,
} from "../../../../../services/utils/index";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import { getAllLinks } from "../../../../../services/api/studydata";
import MatrixView from "../../../../common/MatrixView";
import BasicModal from "../../../../common/BasicModal";
import XpansionPropsView from "./XpansionPropsView";
import CreateCandidateModal from "./CreateCandidateModal";
import CandidateForm from "./CandidateForm";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";

function Candidates() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const navigate = useNavigate();
  const mounted = usePromiseWrapper();
  const [candidateCreationModal, setCandidateCreationModal] =
    useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<string>();
  const [capacityViewModal, setCapacityViewModal] = useState<{
    filename: string;
    content: MatrixType;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const {
    data: candidates,
    isLoading,
    error,
    reload,
  } = usePromiseWithSnackbarError(
    async () => {
      if (!study) {
        return [];
      }

      // Candidates
      const tempCandidates = await getAllCandidates(study.id);
      for (let i = 0; i < tempCandidates.length; i += 1) {
        tempCandidates[i].link = tempCandidates.map((item: { link: string }) =>
          item.link
            .split(" - ")
            .map((index: any) => transformNameToId(index))
            .join(" - ")
        )[i];
      }

      return tempCandidates;
    },
    { errorMessage: t("xpansion:xpansionError"), resetDataOnReload: false },
    [study]
  );

  const { data: capaLinks } = usePromiseWithSnackbarError(
    async () => {
      if (!study) {
        return {};
      }

      return {
        capacities: await getAllCapacities(study.id),
        links: await getAllLinks(study.id),
      };
    },
    t("xpansion:xpansionError"),
    [study]
  );

  const deleteXpansion = async () => {
    try {
      if (study) {
        await mounted(deleteXpansionConfiguration(study.id));
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:deleteXpansionError"), e as AxiosError);
    } finally {
      navigate("../../xpansion");
    }
  };

  const createCandidate = async (candidate: XpansionCandidate) => {
    try {
      if (study) {
        await mounted(addCandidate(study.id, candidate));
        setCandidateCreationModal(false);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:createCandidateError"), e as AxiosError);
    } finally {
      reload();
      setSelectedItem(candidate.name);
    }
  };
  const handleDeleteCandidate = async (name: string | undefined) => {
    if (candidates) {
      try {
        if (study && name) {
          await mounted(deleteCandidate(study.id, name));
        }
      } catch (e) {
        enqueueErrorSnackbar(
          t("xpansion:deleteCandidateError"),
          e as AxiosError
        );
      } finally {
        reload();
        setSelectedItem(undefined);
      }
    }
  };

  const handleUpdateCandidate = async (
    name: string | undefined,
    value: XpansionCandidate | undefined
  ) => {
    try {
      if (study && name && value) {
        await updateCandidate(
          study.id,
          name,
          removeEmptyFields(value as { [key: string]: any }, [
            "link-profile",
            "already-installed-link-profile",
            "already-installed-capacity",
            "max-investments",
            "max-units",
            "unit-size",
          ]) as XpansionCandidate
        );
        enqueueSnackbar(t("studymanager:savedatasuccess"), {
          variant: "success",
        });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:updateCandidateError"), e as AxiosError);
    } finally {
      reload();
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

  const onClose = () => setCandidateCreationModal(false);

  const renderView = () => {
    const candidate = candidates?.find((o) => o.name === selectedItem);
    if (candidate) {
      return (
        <CandidateForm
          candidate={candidate}
          links={capaLinks?.links || []}
          capacities={capaLinks?.capacities || []}
          deleteCandidate={handleDeleteCandidate}
          updateCandidate={handleUpdateCandidate}
          onRead={getOneCapa}
        />
      );
    }
  };

  // TODO
  if (error) {
    return <Box />;
  }

  return (
    <>
      <SplitLayoutView
        left={
          <XpansionPropsView
            candidateList={candidates || []}
            onAdd={() => setCandidateCreationModal(true)}
            selectedItem={selectedItem || ""}
            setSelectedItem={setSelectedItem}
            deleteXpansion={deleteXpansion}
          />
        }
        right={
          <>
            <Box width="100%" height="100%" padding={2} boxSizing="border-box">
              {renderView()}
            </Box>
            <Backdrop
              open={isLoading && !candidates}
              sx={{
                position: "absolute",
                zIndex: (theme) => theme.zIndex.drawer + 1,
                opacity: "0.1 !important",
              }}
            >
              <CircularProgress sx={{ color: "primary.main" }} />
            </Backdrop>
          </>
        }
      />

      {candidateCreationModal && (
        <CreateCandidateModal
          open={candidateCreationModal}
          onClose={onClose}
          onSave={createCandidate}
          links={capaLinks?.links || []}
        />
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

export default Candidates;
