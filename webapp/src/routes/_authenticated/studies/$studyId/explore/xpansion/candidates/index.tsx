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

import DataViewerDialog from "@/components/dialogs/DataViewerDialog";
import SimpleLoader from "@/components/loaders/SimpleLoader";
import type { MatrixDataDTO } from "@/components/Matrix/shared/types";
import EmptyView from "@/components/page/EmptyView";
import SplitView from "@/components/page/SplitView";
import ViewWrapper from "@/components/page/ViewWrapper";
import { getLinks } from "@/services/api/studies/links";
import { Backdrop, Box, CircularProgress } from "@mui/material";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import type { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import type { XpansionCandidate } from "../-shared/types";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";
import {
  addCandidate,
  deleteCandidate,
  deleteXpansionConfiguration,
  getAllCandidates,
  getAllCapacities,
  getCapacity,
  updateCandidate,
  xpansionConfigurationExist,
} from "../../../../../../../services/api/xpansion";
import { nameToId, removeEmptyFields } from "../../../../../../../services/utils/index";
import CandidateForm from "./-components/CandidateForm";
import CreateCandidateDialog from "./-components/CreateCandidateDialog";
import XpansionPropsView from "./-components/XpansionPropsView";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/xpansion/candidates/",
)({
  component: Candidates,
});

function Candidates() {
  const [t] = useTranslation();
  const { studyId } = Route.useParams();
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
      const exist = await xpansionConfigurationExist(studyId);
      if (exist) {
        // Candidates
        const tempCandidates = await getAllCandidates(studyId);
        for (let i = 0; i < tempCandidates.length; i += 1) {
          tempCandidates[i].link = tempCandidates.map((item: { link: string }) =>
            item.link
              .split(" - ")
              .map((index) => nameToId(index))
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
      deps: [studyId],
    },
  );

  const { data: capaLinks, isLoading: isLinksLoading } = usePromiseWithSnackbarError(
    async () => {
      const exist = await xpansionConfigurationExist(studyId);
      if (exist) {
        return {
          capacities: await getAllCapacities(studyId),
          links: await getLinks({ studyId }),
        };
      }
      return {};
    },
    { errorMessage: t("xpansion.error.loadConfiguration"), deps: [studyId] },
  );

  // Handle automatic selection of the first element
  useEffect(() => {
    if (candidates && candidates.length > 0 && !selectedItem) {
      setSelectedItem(candidates[0].name);
    }
  }, [candidates, selectedItem]);

  const deleteXpansion = async () => {
    try {
      await mounted(deleteXpansionConfiguration(studyId));

      navigate({
        to: "/studies/$studyId/explore/xpansion",
        params: { studyId },
        search: { reload: Date.now() },
        replace: true,
      });
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.deleteConfiguration"), e as AxiosError);
    }
  };

  const createCandidate = async (candidate: XpansionCandidate) => {
    try {
      await mounted(addCandidate(studyId, candidate));
      setCandidateCreationDialog(false);
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
        if (name) {
          await mounted(deleteCandidate(studyId, name));
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
      if (name && value) {
        await updateCandidate(
          studyId,
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
      const content = await getCapacity(studyId, filename);
      setCapacityViewDialog({ filename, content });
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
      <SplitView splitId="xpansion">
        <Box sx={{ position: "relative" }}>
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
