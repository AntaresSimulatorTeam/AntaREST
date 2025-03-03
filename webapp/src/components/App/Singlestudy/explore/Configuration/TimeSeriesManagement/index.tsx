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

import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../types/types";
import Form from "../../../../../common/Form";
import type { SubmitHandlerPlus, UseFormReturnPlus } from "../../../../../common/Form/types";
import Fields from "./Fields";
import { useTranslation } from "react-i18next";
import usePromiseHandler from "../../../../../../hooks/usePromiseHandler";
import BuildIcon from "@mui/icons-material/Build";
import { useRef, useState } from "react";
import { setTimeSeriesConfig, generateTimeSeries } from "@/services/api/studies/timeseries";
import { defaultValues, type TimeSeriesConfigValues } from "./utils";

function TimeSeriesManagement() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
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
    return setTimeSeriesConfig({ studyId: study.id, values });
  };

  const handleSubmitSuccessful = async () => {
    setIsLaunchTaskInProgress(true);

    // The WebSocket will trigger an event after the fulfillment of the promise (see `FreezeStudy`)
    await handleGenerateTs({ studyId: study.id });

    setIsLaunchTaskInProgress(false);

    apiRef.current?.reset(defaultValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id}
      config={{
        defaultValues,
        disabled: isLaunchTaskInProgress,
      }}
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
      submitButtonText={t("study.configuration.tsManagement.generateTs")}
      submitButtonIcon={<BuildIcon />}
      apiRef={apiRef}
    >
      <Fields />
    </Form>
  );
}

export default TimeSeriesManagement;
