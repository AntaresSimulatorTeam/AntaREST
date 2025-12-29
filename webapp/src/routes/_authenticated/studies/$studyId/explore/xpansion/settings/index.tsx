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
import ViewWrapper from "@/components/page/ViewWrapper";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import { createFileRoute } from "@tanstack/react-router";
import type { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { XpansionResourceType, type XpansionSettings } from "../-shared/types";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";
import {
  getAllCandidates,
  getAllConstraints,
  getAllWeights,
  getConstraint,
  getWeight,
  getXpansionSettings,
  updateXpansionSettings,
} from "../../../../../../../services/api/xpansion";
import { removeEmptyFields } from "../../../../../../../services/utils/index";
import SettingsForm from "./-components/SettingsForm";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/xpansion/settings/")(
  {
    component: Settings,
  },
);

const resourceContentFetcher = (
  resourceType: string,
): ((uuid: string, filename: string) => Promise<string>) => {
  if (resourceType === XpansionResourceType.constraints) {
    return getConstraint;
  }
  return getWeight;
};

function Settings() {
  const [t] = useTranslation();
  const { studyId } = Route.useParams();
  const [resourceViewDialog, setResourceViewDialog] = useState<{
    filename: string;
    content: string;
    isMatrix: boolean;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const settingsRes = usePromiseWithSnackbarError(() => getXpansionSettings(studyId), {
    errorMessage: t("xpansion.error.loadConfiguration"),
    deps: [studyId],
  });

  const { data: candidates } = usePromiseWithSnackbarError(
    async () => {
      const tempCandidates = await getAllCandidates(studyId);
      return tempCandidates.map((c) => c.name);
    },
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
      resetDataOnReload: false,
      deps: [studyId],
    },
  );

  const { data: constraints } = usePromiseWithSnackbarError(() => getAllConstraints(studyId), {
    errorMessage: t("xpansion.error.loadConfiguration"),
    deps: [studyId],
  });

  const { data: weights } = usePromiseWithSnackbarError(() => getAllWeights(studyId), {
    errorMessage: t("xpansion.error.loadConfiguration"),
    deps: [studyId],
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const updateSettings = async (value: XpansionSettings) => {
    try {
      await updateXpansionSettings(
        studyId,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        removeEmptyFields(value as Record<string, any>, [
          "cut-type",
          "solver",
          "yearly-weights",
          "additional-constraints",
        ]) as XpansionSettings,
      );
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.updateSettings"), e as AxiosError);
    } finally {
      settingsRes.reload();
      enqueueSnackbar(t("studies.success.saveData"), {
        variant: "success",
      });
    }
  };

  const getResourceContent = async (resourceType: string, filename: string) => {
    try {
      const content = await resourceContentFetcher(resourceType)(studyId, filename);
      setResourceViewDialog({
        filename,
        content,
        isMatrix: resourceType === XpansionResourceType.weights,
      });
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.getFile"), e as AxiosError);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <ViewWrapper>
        <UsePromiseCond
          response={settingsRes}
          ifFulfilled={(data) => (
            <SettingsForm
              settings={data}
              candidates={candidates || []}
              constraints={constraints || []}
              weights={weights || []}
              updateSettings={updateSettings}
              onRead={getResourceContent}
            />
          )}
        />
      </ViewWrapper>

      {resourceViewDialog && (
        <DataViewerDialog
          filename={resourceViewDialog.filename}
          content={resourceViewDialog.content}
          onClose={() => setResourceViewDialog(undefined)}
          isMatrix={resourceViewDialog.isMatrix}
        />
      )}
    </>
  );
}
