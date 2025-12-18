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

import NumberFE from "@/components/fieldEditors/NumberFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import useArea from "@/routes/-shared/hook/useArea";
import useStudy from "@/routes/-shared/hook/useStudy";
import { validateNumber } from "@/utils/validation/number";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import {
  COST_GENERATION_OPTIONS,
  THERMAL_GROUPS,
  THERMAL_POLLUTANTS,
  TS_GENERATION_OPTIONS,
  TS_LAW_OPTIONS,
  type ThermalCluster,
  getThermalCluster,
  updateThermalCluster,
} from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/parameters",
)({
  component: Parameters,
});

function Parameters() {
  const study = useStudy();
  const area = useArea();
  const { thermalId } = Route.useParams();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<ThermalCluster>) => {
    return updateThermalCluster(study.id, area.id, thermalId, dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={area.id + thermalId}
      config={{ defaultValues: () => getThermalCluster(study.id, area.id, thermalId) }}
      onSubmit={handleSubmit}
      enableUndoRedo
    >
      {({ control, watch }) => {
        const isCostGenerationEnabled = watch("costGeneration") === "useCostTimeseries";

        return (
          <>
            <Fieldset legend={t("study.modelization.clusters.operatingParameters")}>
              <StringFE label={t("global.name")} name="name" control={control} disabled />
              {semver.lt(study.version, "9.3.0") ? (
                <SelectFE
                  label={t("global.group")}
                  name="group"
                  control={control}
                  options={THERMAL_GROUPS}
                  startCaseLabel={false}
                  sx={{
                    alignSelf: "center",
                  }}
                />
              ) : (
                <StringFE
                  label={t("global.group")}
                  name="group"
                  datalist={THERMAL_GROUPS}
                  control={control}
                />
              )}
              <SwitchFE
                label={t("study.modelization.clusters.enabled")}
                name="enabled"
                control={control}
              />
              <SwitchFE
                label={t("study.modelization.clusters.mustRun")}
                name="mustRun"
                control={control}
              />
              <NumberFE
                label={t("study.modelization.clusters.unitcount")}
                name="unitCount"
                control={control}
                rules={{
                  validate: validateNumber({ min: 1 }),
                  setValueAs: Math.floor,
                }}
              />
              <NumberFE
                label={t("study.modelization.clusters.nominalCapacity")}
                name="nominalCapacity"
                control={control}
                rules={{
                  validate: validateNumber({ min: 0 }),
                }}
              />
              <NumberFE
                label={t("study.modelization.clusters.minStablePower")}
                name="minStablePower"
                control={control}
              />
              <NumberFE
                label={t("study.modelization.clusters.spinning")}
                name="spinning"
                control={control}
                rules={{
                  validate: validateNumber({ min: 0, max: 100 }),
                }}
              />
              <NumberFE
                label={t("study.modelization.clusters.minUpTime")}
                name="minUpTime"
                control={control}
                rules={{
                  validate: validateNumber({ min: 1, max: 168 }),
                  setValueAs: Math.floor,
                }}
              />
              <NumberFE
                label={t("study.modelization.clusters.minDownTime")}
                name="minDownTime"
                control={control}
                rules={{
                  validate: validateNumber({ min: 1, max: 168 }),
                  setValueAs: Math.floor,
                }}
              />
            </Fieldset>
            <Fieldset legend={t("study.modelization.clusters.operatingCosts")}>
              {semver.gte(study.version, "8.7.0") && (
                <>
                  <SelectFE
                    label={t("study.modelization.clusters.costGeneration")}
                    name="costGeneration"
                    options={COST_GENERATION_OPTIONS}
                    control={control}
                  />
                  <NumberFE
                    label={t("study.modelization.clusters.efficiency")}
                    name="efficiency"
                    control={control}
                    rules={{
                      validate: validateNumber({ min: 0 }),
                    }}
                    disabled={!isCostGenerationEnabled}
                  />
                  <NumberFE
                    label={t("study.modelization.clusters.variableOMCost")}
                    name="variableOMCost"
                    control={control}
                    rules={{
                      validate: validateNumber({ min: 0 }),
                    }}
                    disabled={!isCostGenerationEnabled}
                  />
                </>
              )}
              <NumberFE
                label={t("study.modelization.clusters.marginalCost")}
                name="marginalCost"
                control={control}
                rules={{
                  validate: validateNumber({ min: 0 }),
                }}
                disabled={isCostGenerationEnabled}
              />
              <NumberFE
                label={t("study.modelization.clusters.startupCost")}
                name="startupCost"
                control={control}
                rules={{
                  validate: validateNumber({ min: 0 }),
                }}
              />
              <NumberFE
                label={t("study.modelization.clusters.marketBidCost")}
                name="marketBidCost"
                control={control}
                rules={{
                  validate: validateNumber({ min: 0 }),
                }}
                disabled={isCostGenerationEnabled}
              />
              <NumberFE
                label={t("study.modelization.clusters.fixedCost")}
                name="fixedCost"
                control={control}
                rules={{
                  validate: validateNumber({ min: 0 }),
                }}
              />
              <NumberFE
                label={t("study.modelization.clusters.spreadCost")}
                name="spreadCost"
                control={control}
              />
            </Fieldset>
            <Fieldset legend={t("study.modelization.clusters.thermal.pollutants")}>
              {THERMAL_POLLUTANTS.map(
                (name) =>
                  (name === "co2" || semver.gte(study.version, "8.6.0")) && (
                    <NumberFE
                      key={name}
                      label={t(`study.modelization.clusters.thermal.${name}`)}
                      name={name}
                      control={control}
                      rules={{
                        validate: validateNumber({ min: 0 }),
                      }}
                    />
                  ),
              )}
            </Fieldset>
            <Fieldset legend={t("study.modelization.clusters.timeSeriesGen")}>
              <SelectFE
                label={t("study.modelization.clusters.genTs")}
                name="genTs"
                control={control}
                options={TS_GENERATION_OPTIONS}
              />
              <NumberFE
                label={t("study.modelization.clusters.volatilityForced")}
                name="volatilityForced"
                control={control}
                rules={{
                  validate: validateNumber({ min: 0, max: 1 }),
                }}
                slotProps={{
                  htmlInput: {
                    step: 0.1,
                  },
                }}
              />
              <NumberFE
                label={t("study.modelization.clusters.volatilityPlanned")}
                name="volatilityPlanned"
                control={control}
                rules={{
                  validate: validateNumber({ min: 0, max: 1 }),
                }}
                slotProps={{
                  htmlInput: {
                    step: 0.1,
                  },
                }}
              />
              <SelectFE
                label={t("study.modelization.clusters.lawForced")}
                name="lawForced"
                control={control}
                options={TS_LAW_OPTIONS}
              />
              <SelectFE
                label={t("study.modelization.clusters.lawPlanned")}
                name="lawPlanned"
                control={control}
                options={TS_LAW_OPTIONS}
              />
            </Fieldset>
          </>
        );
      }}
    </Form>
  );
}
