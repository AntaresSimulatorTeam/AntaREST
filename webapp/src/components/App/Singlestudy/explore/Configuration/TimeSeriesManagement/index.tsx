/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import type { StudyMetadata } from "../../../../../../common/types";
import Form from "../../../../../common/Form";
import type { SubmitHandlerPlus } from "../../../../../common/Form/types";
import Fields from "./Fields";
import {
  getTimeSeriesFormFields,
  setTimeSeriesFormFields,
  TSFormFields,
} from "./utils";
import { useTranslation } from "react-i18next";
import usePromiseHandler from "../../../../../../hooks/usePromiseHandler";
import { generateTimeSeries } from "../../../../../../services/api/studies/timeseries";
import BuildIcon from "@mui/icons-material/Build";

function TimeSeriesManagement() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();

  const handleGenerateTs = usePromiseHandler({
    fn: generateTimeSeries,
    errorMessage: t("study.configuration.tsManagement.generateTs.error"),
    pendingMessage: t("study.configuration.tsManagement.generateTs.pending"),
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<TSFormFields>) => {
    return setTimeSeriesFormFields(study.id, data.dirtyValues);
  };

  const handleSubmitSuccessful = () => {
    // The WebSocket will trigger an event after the fulfillment of the promise
    handleGenerateTs({ studyId: study.id });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id}
      config={{ defaultValues: () => getTimeSeriesFormFields(study.id) }}
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
      submitButtonText={t("study.configuration.tsManagement.generateTs")}
      submitButtonIcon={<BuildIcon />}
      allowSubmitOnPristine
    >
      <Fields />
    </Form>
  );
}

export default TimeSeriesManagement;
