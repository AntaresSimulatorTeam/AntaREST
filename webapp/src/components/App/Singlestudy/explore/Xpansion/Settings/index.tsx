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

import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import type { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import type { StudyMetadata } from "../../../../../../types/types";
import { XpansionResourceType, type XpansionSettings } from "../types";
import {
  getXpansionSettings,
  getAllConstraints,
  getConstraint,
  updateXpansionSettings,
  getAllWeights,
  getWeight,
  getAllCandidates,
} from "../../../../../../services/api/xpansion";
import SettingsForm from "./SettingsForm";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import { removeEmptyFields } from "../../../../../../services/utils/index";
import DataViewerDialog from "../../../../../common/dialogs/DataViewerDialog";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import UsePromiseCond from "@/components/common/utils/UsePromiseCond";

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
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [resourceViewDialog, setResourceViewDialog] = useState<{
    filename: string;
    content: string;
    isMatrix: boolean;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const settingsRes = usePromiseWithSnackbarError(
    async () => {
      if (study) {
        return getXpansionSettings(study.id);
      }
    },
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
    },
  );

  const { data: candidates } = usePromiseWithSnackbarError(
    async () => {
      if (!study) {
        return [];
      }
      const tempCandidates = await getAllCandidates(study.id);
      return tempCandidates.map((c) => c.name);
    },
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
      resetDataOnReload: false,
      deps: [study],
    },
  );

  const { data: constraints } = usePromiseWithSnackbarError(
    async () => {
      if (study) {
        return getAllConstraints(study.id);
      }
    },
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
    },
  );

  const { data: weights } = usePromiseWithSnackbarError(
    async () => {
      if (study) {
        return getAllWeights(study.id);
      }
    },
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
    },
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const updateSettings = async (value: XpansionSettings) => {
    try {
      if (study) {
        await updateXpansionSettings(
          study.id,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          removeEmptyFields(value as Record<string, any>, [
            "cut-type",
            "solver",
            "yearly-weights",
            "additional-constraints",
          ]) as XpansionSettings,
        );
      }
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
      if (study) {
        const content = await resourceContentFetcher(resourceType)(study.id, filename);
        setResourceViewDialog({
          filename,
          content,
          isMatrix: resourceType === XpansionResourceType.weights,
        });
      }
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

export default Settings;
