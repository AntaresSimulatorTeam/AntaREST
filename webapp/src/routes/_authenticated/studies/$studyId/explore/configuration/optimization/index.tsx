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

import SelectFE from "@/components/fieldEditors/SelectFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import ViewWrapper from "@/components/page/ViewWrapper";
import {
  getOptimizationForm,
  setOptimizationForm,
} from "@/services/api/studies/config/optimization";
import type { OptimizationForm } from "@/services/api/studies/config/optimization/types";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import useStudy from "../../../../../../-shared/hook/useStudy";
import {
  EXPORT_MPS_OPTIONS,
  LEGACY_TRANSMISSION_CAPACITIES_OPTIONS,
  SIMPLEX_OPTIMIZATION_RANGE_OPTIONS,
  TRANSMISSION_CAPACITIES_OPTIONS,
  UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS,
} from "./-constants";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/configuration/optimization/",
)({
  component: Optimization,
});

function Optimization() {
  const { t } = useTranslation();
  const study = useStudy();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<OptimizationForm>) => {
    return setOptimizationForm({
      studyId: study.id,
      values: dirtyValues,
      studyVersion: study.version,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <Form
        config={{
          defaultValues: () =>
            getOptimizationForm({ studyId: study.id, studyVersion: study.version }),
        }}
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
              {semver.gte(study.version, "8.3.0") ? (
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
              {semver.gte(study.version, "8.4.0") ? (
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
    </ViewWrapper>
  );
}
