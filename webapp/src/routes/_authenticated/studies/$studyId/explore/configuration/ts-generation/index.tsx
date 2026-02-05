/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import Form from "@/components/Form";
import type { SubmitHandlerPlus, UseFormReturnPlus } from "@/components/Form/types";
import ViewWrapper from "@/components/page/ViewWrapper";
import { generateTimeSeries, setTimeSeriesConfig } from "@/services/api/studies/timeseries";
import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import usePromiseHandler from "../../../../../../../hooks/usePromiseHandler";
import Fields from "./-components/Fields";
import { defaultValues, type TimeSeriesConfigValues } from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/configuration/ts-generation/",
)({
  component: TimeSeriesGeneration,
});

function TimeSeriesGeneration() {
  const { studyId } = Route.useParams();
  const { t } = useTranslation();
  const [isLaunchTaskInProgress, setIsLaunchTaskInProgress] = useState(false);
  const apiRef = useRef<UseFormReturnPlus<TimeSeriesConfigValues>>(null);

  const handleGenerateTs = usePromiseHandler({
    fn: generateTimeSeries,
    errorMessage: t("study.configuration.tsManagement.generateTs.error"),
    pendingMessage: t("study.configuration.tsManagement.generateTs.pending"),
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<TimeSeriesConfigValues>) => {
    return setTimeSeriesConfig({ studyId, values });
  };

  const handleSubmitSuccessful = async ({ values }: SubmitHandlerPlus<TimeSeriesConfigValues>) => {
    setIsLaunchTaskInProgress(true);

    // The WebSocket will trigger an event after the fulfillment of the promise (see `FreezeStudy`)
    await handleGenerateTs({ studyId, outageDetails: values.thermal.outageDetails });

    setIsLaunchTaskInProgress(false);

    apiRef.current?.reset(defaultValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <Form
        config={{
          defaultValues,
          disabled: isLaunchTaskInProgress,
        }}
        onSubmit={handleSubmit}
        onSubmitSuccessful={handleSubmitSuccessful}
        apiRef={apiRef}
        hideSubmitButton
      >
        <Fields />
      </Form>
    </ViewWrapper>
  );
}
