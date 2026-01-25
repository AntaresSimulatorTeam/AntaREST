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

import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import NumberFE from "@/components/fieldEditors/NumberFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { validateNumber } from "@/utils/validation/number";
import { Box, Tooltip } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import {
  convertPercentageToRatio,
  convertRatioToPercentage,
  type FormalizedStorage,
  getStorage,
  STORAGE_GROUPS,
  updateStorage,
} from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/parameters",
)({
  component: Parameters,
});

function Parameters() {
  const study = useStudy();
  const { areaId, storageId } = Route.useParams();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Config
  ////////////////////////////////////////////////////////////////

  const getDefaultValues = async () => {
    const storage = await getStorage(study.id, areaId, storageId);
    return convertRatioToPercentage(storage);
  };

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ dirtyValues }: SubmitHandlerPlus<FormalizedStorage>) => {
    const updatedStorage = await updateStorage(
      study.id,
      areaId,
      storageId,
      convertPercentageToRatio(dirtyValues),
    );

    return convertRatioToPercentage(updatedStorage);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={areaId + storageId}
      config={{ defaultValues: getDefaultValues }}
      onSubmit={handleSubmit}
      enableUndoRedo
    >
      {({ control }) => (
        <>
          <Fieldset legend={t("study.modeling.clusters.operatingParameters")}>
            <StringFE label={t("global.name")} name="name" control={control} disabled />
            {semver.lt(study.version, "9.2.0") ? (
              <SelectFE
                label={t("global.group")}
                name="group"
                control={control}
                options={STORAGE_GROUPS}
                startCaseLabel={false}
                sx={{
                  alignSelf: "center",
                }}
              />
            ) : (
              <StringFE
                label={t("global.group")}
                name="group"
                datalist={STORAGE_GROUPS}
                control={control}
              />
            )}
            {semver.gte(study.version, "8.8.0") && (
              <SwitchFE label={t("global.enabled")} name="enabled" control={control} />
            )}
            <Fieldset.Break />
            <Tooltip
              title={t("study.modeling.storages.reservoirCapacity.info")}
              arrow
              placement="top"
            >
              <Box>
                <NumberFE
                  label={t("study.modeling.storages.reservoirCapacity")}
                  name="reservoirCapacity"
                  control={control}
                  rules={{
                    validate: validateNumber({ min: 0 }),
                  }}
                />
              </Box>
            </Tooltip>
            <NumberFE
              label={t("study.modeling.storages.initialLevel")}
              name="initialLevel"
              control={control}
              rules={{
                validate: validateNumber({ min: 0, max: 100 }),
              }}
            />
            <SwitchFE
              label={t("study.modeling.storages.initialLevelOptim")}
              name="initialLevelOptim"
              control={control}
              sx={{
                alignItems: "center",
                alignSelf: "center",
                width: 2,
              }}
            />
            {semver.gte(study.version, "9.3.0") && (
              <SwitchFE
                label={t("study.modeling.storages.allowOverflow")}
                name="allowOverflow"
                control={control}
              />
            )}
          </Fieldset>
          <Fieldset legend={t("study.modeling.storages.injectionParameters")}>
            <Tooltip
              title={t("study.modeling.storages.injectionNominalCapacity.info")}
              arrow
              placement="top"
            >
              <Box>
                <NumberFE
                  label={t("study.modeling.storages.injectionNominalCapacity")}
                  name="injectionNominalCapacity"
                  control={control}
                  rules={{
                    validate: validateNumber({ min: 0 }),
                  }}
                />
              </Box>
            </Tooltip>
            {/*
              Efficiency cross-validation (v9.2.0+):
              Injection ≤ withdrawal efficiency (prevents energy creation).
              Bidirectional validation. Pre-9.2.0: single efficiency field capped at 100%.
            */}
            <NumberFE
              label={t("study.modeling.storages.efficiency")}
              name="efficiency"
              control={control}
              rules={{
                ...(semver.gte(studyVersion, "9.2.0") && { deps: ["efficiencyWithdrawal"] }),
                validate: (value, formValues) => {
                  const numValidation = validateNumber({
                    min: 0,
                    max: semver.gte(studyVersion, "9.2.0") ? undefined : 100,
                  })(value);

                  if (numValidation !== true) {
                    return numValidation;
                  }

                  if (
                    semver.gte(studyVersion, "9.2.0") &&
                    value > formValues.efficiencyWithdrawal
                  ) {
                    return t("study.modelization.storages.error.efficiencyTooHigh");
                  }

                  return true;
                },
              }}
            />
            {semver.gte(study.version, "9.2.0") && (
              <SwitchFE
                label={t("study.modeling.storages.penalizeVariationInjection")}
                name="penalizeVariationInjection"
                control={control}
              />
            )}
          </Fieldset>
          <Fieldset legend={t("study.modeling.storages.withdrawalParameters")}>
            <Tooltip
              title={t("study.modeling.storages.withdrawalNominalCapacity.info")}
              arrow
              placement="top"
            >
              <Box>
                <NumberFE
                  label={t("study.modeling.storages.withdrawalNominalCapacity")}
                  name="withdrawalNominalCapacity"
                  control={control}
                  rules={{
                    validate: validateNumber({ min: 0 }),
                  }}
                />
              </Box>
            </Tooltip>
            {semver.gte(study.version, "9.2.0") && (
              <>
                <Tooltip
                  title={t("study.modeling.storages.efficiencyWithdrawal.info")}
                  arrow
                  placement="top"
                >
                  <Box>
                    <NumberFE
                      label={t("study.modeling.storages.efficiencyWithdrawal")}
                      name="efficiencyWithdrawal"
                      control={control}
                      rules={{
                        deps: ["efficiency"],
                        validate: validateNumber({
                          min: 0,
                        }),
                      }}
                    />
                  </Box>
                </Tooltip>
                <SwitchFE
                  label={t("study.modeling.storages.penalizeVariationWithdrawal")}
                  name="penalizeVariationWithdrawal"
                  control={control}
                />
              </>
            )}
          </Fieldset>
        </>
      )}
    </Form>
  );
}
