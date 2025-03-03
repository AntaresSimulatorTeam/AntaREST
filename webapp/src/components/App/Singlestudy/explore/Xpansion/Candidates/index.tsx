/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { useEffect, useState } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import type { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Backdrop, Box, CircularProgress } from "@mui/material";
import { usePromise as usePromiseWrapper } from "react-use";
import { useSnackbar } from "notistack";
import type { StudyMetadata } from "../../../../../../types/types";
import type { XpansionCandidate } from "../types";
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
import { transformNameToId, removeEmptyFields } from "../../../../../../services/utils/index";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import XpansionPropsView from "./XpansionPropsView";
import CreateCandidateDialog from "./CreateCandidateDialog";
import CandidateForm from "./CandidateForm";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import DataViewerDialog from "../../../../../common/dialogs/DataViewerDialog";
import EmptyView from "../../../../../common/page/EmptyView";
import SplitView from "../../../../../common/SplitView";
import { getLinks } from "@/services/api/studies/links";
import type { MatrixDataDTO } from "@/components/common/Matrix/shared/types";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import SimpleLoader from "@/components/common/loaders/SimpleLoader";

function Candidates() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const navigate = useNavigate();
  const mounted = usePromiseWrapper();
  const [candidateCreationDialog, setCandidateCreationDialog] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<string>();
  const [capacityViewDialog, setCapacityViewDialog] = useState<{
    filename: string;
    content: MatrixDataDTO;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const {
    data: candidates,
    isLoading: isCandidatesLoading,
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
          tempCandidates[i].link = tempCandidates.map((item: { link: string }) =>
            item.link
              .split(" - ")
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              .map((index: any) => transformNameToId(index))
              .join(" - "),
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
    },
  );

  const { data: capaLinks, isLoading: isLinksLoading } = usePromiseWithSnackbarError(
    async () => {
      if (!study) {
        return {};
      }
      const exist = await xpansionConfigurationExist(study.id);
      if (exist) {
        return {
          capacities: await getAllCapacities(study.id),
          links: await getLinks({ studyId: study.id }),
        };
      }
      return {};
    },
    { errorMessage: t("xpansion.error.loadConfiguration"), deps: [study] },
  );

  // Handle automatic selection of the first element
  useEffect(() => {
    if (candidates && candidates.length > 0 && !selectedItem) {
      setSelectedItem(candidates[0].name);
    }
  }, [candidates, selectedItem]);

  const deleteXpansion = async () => {
    try {
      if (study) {
        await mounted(deleteXpansionConfiguration(study.id));
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.deleteConfiguration"), e as AxiosError);
    } finally {
      navigate("../../xpansion", { state: { exist: false } });
    }
  };

  const createCandidate = async (candidate: XpansionCandidate) => {
    try {
      if (study) {
        await mounted(addCandidate(study.id, candidate));
        setCandidateCreationDialog(false);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.createCandidate"), e as AxiosError);
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
        enqueueErrorSnackbar(t("xpansion.error.deleteCandidate"), e as AxiosError);
      } finally {
        reload();
        setSelectedItem(undefined);
      }
    }
  };

  const handleUpdateCandidate = async (
    name: string | undefined,
    value: XpansionCandidate | undefined,
  ) => {
    try {
      if (study && name && value) {
        await updateCandidate(
          study.id,
          name,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          removeEmptyFields(value as Record<string, any>, [
            "link-profile",
            "already-installed-link-profile",
            "already-installed-capacity",
            "max-investments",
            "max-units",
            "unit-size",
          ]) as XpansionCandidate,
        );
        enqueueSnackbar(t("studies.success.saveData"), {
          variant: "success",
        });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.updateCandidate"), e as AxiosError);
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

  if (isCandidatesLoading || isLinksLoading) {
    return <SimpleLoader />;
  }

  if (isRejected) {
    return <EmptyView title={t("xpansion.error.loadConfiguration")} />;
  }

  return (
    <>
      <SplitView id="xpansion" sizes={[10, 90]}>
        <Box>
          <XpansionPropsView
            candidateList={candidates || []}
            onAdd={() => setCandidateCreationDialog(true)}
            selectedItem={selectedItem || ""}
            setSelectedItem={setSelectedItem}
            deleteXpansion={deleteXpansion}
          />
        </Box>
        <Box>
          <ViewWrapper>
            {!candidates?.length ? (
              <EmptyView title={t("xpansion.candidates.empty")} />
            ) : (
              renderView()
            )}
          </ViewWrapper>
          <Backdrop
            open={isCandidatesLoading && !candidates}
            sx={{
              position: "absolute",
              zIndex: (theme) => theme.zIndex.drawer + 1,
              opacity: "0.1 !important",
            }}
          >
            <CircularProgress sx={{ color: "primary.main" }} />
          </Backdrop>
        </Box>
      </SplitView>

      {candidateCreationDialog && (
        <CreateCandidateDialog
          open={candidateCreationDialog}
          onClose={onClose}
          onSave={createCandidate}
          links={capaLinks?.links || []}
          candidates={candidates ?? []}
        />
      )}
      {!!capacityViewDialog && (
        <DataViewerDialog
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
