/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react-hooks/exhaustive-deps */
import { useCallback, useEffect, useState } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { useSnackbar } from "notistack";
import {
  MatrixType,
  StudyMetadata,
  XpansionCandidate,
  LinkCreationInfo,
} from "../../../../../common/types";
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
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import MatrixView from "../../../../common/MatrixView";
import BasicModal from "../../../../common/BasicModal";
import XpansionPropsView from "./XpansionPropsView";
import CreateCandidateModal from "./CreateCandidateModal";
import CandidateForm from "./CandidateForm";

function Candidates() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const navigate = useNavigate();
  const [candidateCreationModal, setCandidateCreationModal] =
    useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<string>();
  const [candidates, setCandidates] = useState<Array<XpansionCandidate>>();
  const [links, setLinks] = useState<Array<LinkCreationInfo>>();
  const [capacities, setCapacities] = useState<Array<string>>();
  const [loaded, setLoaded] = useState<boolean>(false);
  const [capacityViewModal, setCapacityViewModal] = useState<{
    filename: string;
    content: MatrixType;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const initCandidate = useCallback(
    async (
      after: () => void = () => {
        /* noop */
      }
    ) => {
      try {
        if (study) {
          const tempCandidates = await getAllCandidates(study.id);
          for (let i = 0; i < tempCandidates.length; i += 1) {
            tempCandidates[i].link = tempCandidates.map(
              (item: { link: string }) =>
                item.link
                  .split(" - ")
                  .map((index: any) => transformNameToId(index))
                  .join(" - ")
            )[i];
          }
          setCandidates(tempCandidates);
        }
        if (after) {
          after();
        }
      } catch (e) {
        enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
      }
    },
    [study?.id, t]
  );

  const initCapa = useCallback(async () => {
    try {
      if (study) {
        const tempCapa = await getAllCapacities(study.id);
        setCapacities(tempCapa);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
    }
  }, [study?.id, t]);

  const init = useCallback(async () => {
    try {
      if (study) {
        initCandidate();
        initCapa();
        const tempLinks = await getAllLinks(study.id);
        setLinks(tempLinks);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:xpansionError"), e as AxiosError);
    } finally {
      setLoaded(true);
    }
  }, [study?.id, t, initCandidate, initCapa]);

  const deleteXpansion = async () => {
    try {
      if (study) {
        await deleteXpansionConfiguration(study.id);
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
        await addCandidate(study.id, candidate);
        setCandidateCreationModal(false);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:createCandidateError"), e as AxiosError);
    } finally {
      initCandidate(() => {
        setSelectedItem(candidate.name);
      });
    }
  };

  const handleDeleteCandidate = async (name: string) => {
    if (candidates) {
      const obj = candidates.filter((o) => o.name !== name);
      try {
        if (study) {
          await deleteCandidate(study.id, name);
          setCandidates(obj);
          setSelectedItem(undefined);
        }
      } catch (e) {
        enqueueErrorSnackbar(
          t("xpansion:deleteCandidateError"),
          e as AxiosError
        );
      } finally {
        initCandidate();
      }
    }
  };

  const handleUpdateCandidate = async (
    name: string,
    value: XpansionCandidate
  ) => {
    try {
      if (study) {
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
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion:updateCandidateError"), e as AxiosError);
    } finally {
      if (name && value["annual-cost-per-mw"] && value.link) {
        if (
          (value["max-investment"] && value["max-investment"] >= 0) ||
          (value["max-units"] &&
            value["max-units"] >= 0 &&
            value["unit-size"] &&
            value["unit-size"] >= 0)
        ) {
          initCandidate(() => setSelectedItem(value.name));
          if (
            (value["max-investment"] &&
              !value["max-units"] &&
              !value["unit-size"]) ||
            (!value["max-investment"] &&
              value["max-units"] &&
              value["unit-size"])
          ) {
            enqueueSnackbar(t("studymanager:savedatasuccess"), {
              variant: "success",
            });
          }
        }
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

  useEffect(() => {
    init();
  }, [init, setSelectedItem]);

  const onClose = () => setCandidateCreationModal(false);

  const renderView = () => {
    if (candidates) {
      const candidate = candidates.find((o) => o.name === selectedItem);
      if (candidate) {
        return (
          <CandidateForm
            candidate={candidate}
            links={links || []}
            capacities={capacities || []}
            deleteCandidate={handleDeleteCandidate}
            updateCandidate={handleUpdateCandidate}
            onRead={getOneCapa}
          />
        );
      }
    }
    return <Box />;
  };

  return (
    <>
      {loaded ? (
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
            <Box width="100%" height="100%" padding={2} boxSizing="border-box">
              {renderView()}
            </Box>
          }
        />
      ) : (
        <SimpleLoader />
      )}

      {candidateCreationModal && (
        <CreateCandidateModal
          open={candidateCreationModal}
          onClose={onClose}
          onSave={createCandidate}
          links={links || []}
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
