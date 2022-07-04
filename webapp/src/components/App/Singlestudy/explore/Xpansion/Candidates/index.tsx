/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Backdrop, Box, CircularProgress } from "@mui/material";
import { usePromise as usePromiseWrapper } from "react-use";
import { useSnackbar } from "notistack";
import { MatrixType, StudyMetadata } from "../../../../../../common/types";
import { XpansionCandidate } from "../types";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import {
  getAllCandidates,
  getAllCapacities,
  deleteXpansionConfiguration,
  addCandidate,
  deleteCandidate,
  updateCandidate,
  getCapacity,
  xpansionConfigurationExist,
} from "../../../../../../services/api/xpansion";
import {
  transformNameToId,
  removeEmptyFields,
} from "../../../../../../services/utils/index";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import { getAllLinks } from "../../../../../../services/api/studydata";
import XpansionPropsView from "./XpansionPropsView";
import CreateCandidateDialog from "./CreateCandidateDialog";
import CandidateForm from "./CandidateForm";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import DataViewerDialog from "../../../../../common/dialogs/DataViewerDialog";

function Candidates() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const navigate = useNavigate();
  const mounted = usePromiseWrapper();
  const [candidateCreationDialog, setCandidateCreationDialog] =
    useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<string>();
  const [capacityViewDialog, setCapacityViewDialog] = useState<{
    filename: string;
    content: MatrixType;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const {
    data: candidates,
    isLoading,
    isRejected,
    reload,
  } = usePromiseWithSnackbarError(
    async () => {
      if (!study) {
        return [];
      }
      const exist = await xpansionConfigurationExist(study.id);
      if (exist) {
        // Candidates
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
        return tempCandidates;
      }
      return [];
    },
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
      resetDataOnReload: false,
      deps: [study],
    }
  );

  const { data: capaLinks } = usePromiseWithSnackbarError(
    async () => {
      if (!study) {
        return {};
      }
      const exist = await xpansionConfigurationExist(study.id);
      if (exist) {
        return {
          capacities: await getAllCapacities(study.id),
          links: await getAllLinks({ uuid: study.id }),
        };
      }
      return {};
    },
    { errorMessage: t("xpansion.error.loadConfiguration"), deps: [study] }
  );

  const deleteXpansion = async () => {
    try {
      if (study) {
        await mounted(deleteXpansionConfiguration(study.id));
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t("xpansion.error.deleteConfiguration"),
        e as AxiosError
      );
    } finally {
      navigate("../../xpansion");
    }
  };

  const createCandidate = async (candidate: XpansionCandidate) => {
    try {
      if (study) {
        await mounted(addCandidate(study.id, candidate));
        setCandidateCreationDialog(false);
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t("xpansion.error.createCandidate"),
        e as AxiosError
      );
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
          t("xpansion.error.deleteCandidate"),
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
        enqueueSnackbar(t("studies.success.saveData"), {
          variant: "success",
        });
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t("xpansion.error.updateCandidate"),
        e as AxiosError
      );
    } finally {
      reload();
    }
  };

  const getOneCapa = async (filename: string) => {
    try {
      if (study) {
        const content = await getCapacity(study.id, filename);
        setCapacityViewDialog({ filename, content });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.getFile"), e as AxiosError);
    }
  };

  const onClose = () => setCandidateCreationDialog(false);

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
  if (isRejected) {
    return <Box />;
  }

  return (
    <>
      <SplitLayoutView
        left={
          <XpansionPropsView
            candidateList={candidates || []}
            onAdd={() => setCandidateCreationDialog(true)}
            selectedItem={selectedItem || ""}
            setSelectedItem={setSelectedItem}
            deleteXpansion={deleteXpansion}
          />
        }
        right={
          <>
            <Box width="100%" height="100%" boxSizing="border-box">
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

      {candidateCreationDialog && (
        <CreateCandidateDialog
          open={candidateCreationDialog}
          onClose={onClose}
          onSave={createCandidate}
          links={capaLinks?.links || []}
        />
      )}
      {!!capacityViewDialog && (
        <DataViewerDialog
          studyId={study?.id || ""}
          filename={capacityViewDialog.filename}
          content={capacityViewDialog.content}
          onClose={() => setCapacityViewDialog(undefined)}
          isMatrix
        />
      )}
    </>
  );
}

export default Candidates;
