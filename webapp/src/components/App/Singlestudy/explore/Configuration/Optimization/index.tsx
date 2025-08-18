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

import SelectFE from "@/components/common/fieldEditors/SelectFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import Fieldset from "@/components/common/Fieldset";
import {
  getOptimizationFormFields,
  setOptimizationFormFields,
} from "@/services/api/studies/config/optimization";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../types/types";
import Form from "../../../../../common/Form";
import type { SubmitHandlerPlus } from "../../../../../common/Form/types";
import {
  EXPORT_MPS_OPTIONS,
  formatValuesForApi,
  formatValuesForForm,
  LEGACY_TRANSMISSION_CAPACITIES_OPTIONS,
  SIMPLEX_OPTIMIZATION_RANGE_OPTIONS,
  TRANSMISSION_CAPACITIES_OPTIONS,
  UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS,
  type FormattedOptimizationFormFields,
} from "./utils";

function Optimization() {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const studyVersion = Number(study.version);

  const getDefaultValues = async () => {
    const values = await getOptimizationFormFields({
      studyId: study.id,
    });

    return formatValuesForForm(values, studyVersion);
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({
    dirtyValues,
  }: SubmitHandlerPlus<FormattedOptimizationFormFields>) => {
    const updatedValues = await setOptimizationFormFields({
      studyId: study.id,
      values: formatValuesForApi(dirtyValues),
    });

    return formatValuesForForm(updatedValues, studyVersion);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id}
      config={{ defaultValues: getDefaultValues }}
      onSubmit={handleSubmit}
      enableUndoRedo
    >
      {({ control }) => (
        <>
          <Fieldset legend={t("study.configuration.optimization.legend.general")}>
            <SelectFE
              label={t("study.configuration.optimization.unfeasibleProblemBehavior")}
              options={UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS}
              name="unfeasibleProblemBehavior"
              control={control}
            />
            <SelectFE
              label={t("study.configuration.optimization.simplexOptimizationRange")}
              options={SIMPLEX_OPTIMIZATION_RANGE_OPTIONS}
              name="simplexOptimizationRange"
              control={control}
            />
            {studyVersion >= 830 ? (
              <SelectFE
                label={t("study.configuration.optimization.exportMps")}
                options={EXPORT_MPS_OPTIONS}
                name="exportMps"
                control={control}
              />
            ) : (
              <SwitchFE
                label={t("study.configuration.optimization.exportMps")}
                name="exportMps"
                control={control}
              />
            )}
            <SwitchFE
              label={t("study.configuration.optimization.bindingConstraints")}
              name="bindingConstraints"
              control={control}
            />
            <SwitchFE
              label={t("study.configuration.optimization.hurdleCosts")}
              name="hurdleCosts"
              control={control}
            />
          </Fieldset>
          <Fieldset legend={t("study.configuration.optimization.legend.links")}>
            {studyVersion >= 840 ? (
              <SelectFE
                label={t("study.configuration.optimization.transmissionCapacities")}
                options={TRANSMISSION_CAPACITIES_OPTIONS}
                name="transmissionCapacities"
                control={control}
              />
            ) : (
              <SelectFE
                label={t("study.configuration.optimization.transmissionCapacities")}
                options={LEGACY_TRANSMISSION_CAPACITIES_OPTIONS}
                name="transmissionCapacities"
                control={control}
              />
            )}
          </Fieldset>
          <Fieldset legend={t("study.configuration.optimization.legend.thermalClusters")}>
            <SwitchFE
              label={t("study.configuration.optimization.thermalClustersMinStablePower")}
              name="thermalClustersMinStablePower"
              control={control}
            />
            <SwitchFE
              label={t("study.configuration.optimization.thermalClustersMinUdTime")}
              name="thermalClustersMinUdTime"
              control={control}
            />
          </Fieldset>
          <Fieldset legend={t("study.configuration.optimization.legend.reserve")}>
            <SwitchFE
              label={t("study.configuration.optimization.dayAheadReserve")}
              name="dayAheadReserve"
              control={control}
            />
            <SwitchFE
              label={t("study.configuration.optimization.primaryReserve")}
              name="primaryReserve"
              control={control}
            />
            <SwitchFE
              label={t("study.configuration.optimization.strategicReserve")}
              name="strategicReserve"
              control={control}
            />
            <SwitchFE
              label={t("study.configuration.optimization.spinningReserve")}
              name="spinningReserve"
              control={control}
            />
          </Fieldset>
        </>
      )}
    </Form>
  );
}

export default Optimization;
