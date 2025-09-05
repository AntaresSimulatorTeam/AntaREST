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

import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { updateScenarioBuilderForm } from "@/services/api/studies/config/scenarioBuilder";
import type {
  ScenarioDisplay,
  ScenarioType,
} from "@/services/api/studies/config/scenarioBuilder/types";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import type { StudyMetadata } from "../../../../../../../../types/types";
import { toError } from "../../../../../../../../utils/fnUtils";
import type { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import EmptyView from "../../../../../../../common/page/EmptyView";
import TableForm from "../../../../../../../common/TableForm";

interface Props {
  config: ScenarioDisplay;
  type: ScenarioType;
  areaId?: string;
}

function Table({ config, type, areaId }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ dirtyValues }: SubmitHandlerPlus) => {
    try {
      await updateScenarioBuilderForm({
        studyId: study.id,
        scenarioType: type,
        values: dirtyValues,
        areaId,
      });
    } catch (error) {
      enqueueErrorSnackbar(
        t("study.configuration.general.mcScenarioBuilder.update.error", {
          type,
        }),
        toError(error),
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (Object.keys(config).length === 0) {
    return <EmptyView title="No scenario configuration." />;
  }

  return (
    <TableForm
      key={JSON.stringify(config)}
      autoSubmit={false}
      defaultValues={config}
      tableProps={{
        type: "numeric",
        placeholder: "rand",
        allowEmpty: true,
        colHeaders: (index) => `${t("global.year")} ${index + 1}`,
        className: "htCenter",
      }}
      onSubmit={handleSubmit}
    />
  );
}

export default Table;
