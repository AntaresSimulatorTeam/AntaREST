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
import type { Area, Cluster, StudyMetadata } from "../../../../../../../../types/types";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../../common/Fieldset";
import Form from "../../../../../../../common/Form";
import {
  COST_GENERATION_OPTIONS,
  THERMAL_GROUPS,
  THERMAL_POLLUTANTS,
  TS_GENERATION_OPTIONS,
  TS_LAW_OPTIONS,
  type ThermalCluster,
  getThermalCluster,
  updateThermalCluster,
} from "../utils";
import { validateNumber } from "@/utils/validation/number";
import { useCallback } from "react";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";

interface Props {
  study: StudyMetadata;
  areaId: Area["name"];
  clusterId: Cluster["id"];
}

function ThermalForm({ study, areaId, clusterId }: Props) {
  const { t } = useTranslation();
  const studyVersion = Number(study.version);

  // Prevents re-fetch while `useNavigateOnCondition` event occurs in parent component
  const defaultValues = useCallback(() => getThermalCluster(study.id, areaId, clusterId), []);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<ThermalCluster>) => {
    return updateThermalCluster(study.id, areaId, clusterId, dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id + areaId}
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      enableUndoRedo
      disableStickyFooter
      hideFooterDivider
    >
      {({ control, watch }) => {
        const isCostGenerationEnabled = watch("costGeneration") === "useCostTimeseries";

        return (
          <>
            <Fieldset legend={t("global.general")}>
              <StringFE label={t("global.name")} name="name" control={control} disabled />
              <SelectFE
                label={t("global.group")}
                name="group"
                control={control}
                options={THERMAL_GROUPS}
                startCaseLabel={false}
              />
            </Fieldset>
            <Fieldset legend={t("study.modelization.clusters.operatingParameters")}>
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
              {studyVersion >= 870 && (
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
                  (name === "co2" || studyVersion >= 860) && (
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

export default ThermalForm;
