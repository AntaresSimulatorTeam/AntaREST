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
import { validateNumber } from "@/utils/validation/number";
import { Box, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../types/types";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../common/Form";
import { PRICE_TAKING_ORDER_OPTIONS, type AdequacyPatchFormFields } from "./utils";

function Fields() {
  const { t } = useTranslation();
  const { control } = useFormContextPlus<AdequacyPatchFormFields>();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const studyVersion = Number(study.version);

  return (
    <Box>
      <Fieldset fullFieldWidth>
        <SwitchFE
          label={t("study.configuration.adequacyPatch.enableAdequacyPatch")}
          name="enableAdequacyPatch"
          control={control}
        />
      </Fieldset>
      <Fieldset
        legend={
          <Tooltip
            title={t("study.configuration.adequacyPatch.legend.localMatchingRule.tooltip", {
              defaultValue: "",
            })}
          >
            <span>{t("study.configuration.adequacyPatch.legend.localMatchingRule")}</span>
          </Tooltip>
        }
        fullFieldWidth
      >
        <SwitchFE
          label={t(
            "study.configuration.adequacyPatch.ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch",
          )}
          name="ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch"
          control={control}
        />
      </Fieldset>
      {studyVersion >= 850 && (
        <>
          <Fieldset
            legend={
              <Tooltip
                title={t("study.configuration.adequacyPatch.legend.curtailmentSharing.tooltip", {
                  defaultValue: "",
                })}
              >
                <span>{t("study.configuration.adequacyPatch.legend.curtailmentSharing")}</span>
              </Tooltip>
            }
          >
            <SelectFE
              label={t("study.configuration.adequacyPatch.priceTakingOrder")}
              options={PRICE_TAKING_ORDER_OPTIONS}
              name="priceTakingOrder"
              control={control}
            />
            <Tooltip
              title={t("study.configuration.adequacyPatch.includeHurdleCostCsr.tooltip", {
                defaultValue: "",
              })}
            >
              <span>
                <SwitchFE
                  label={t("study.configuration.adequacyPatch.includeHurdleCostCsr")}
                  sx={{ textWrap: "nowrap" }}
                  name="includeHurdleCostCsr"
                  control={control}
                />
              </span>
            </Tooltip>
          </Fieldset>

          <Fieldset
            legend={t("study.configuration.adequacyPatch.legend.advanced")}
            fieldWidth={500}
          >
            <Tooltip
              title={t(
                "study.configuration.adequacyPatch.thresholdInitiateCurtailmentSharingRule.tooltip",
                { defaultValue: "" },
              )}
            >
              <span>
                <NumberFE
                  label={t(
                    "study.configuration.adequacyPatch.thresholdInitiateCurtailmentSharingRule",
                  )}
                  name="thresholdInitiateCurtailmentSharingRule"
                  control={control}
                  rules={{
                    validate: validateNumber({ min: 0 }),
                  }}
                />
              </span>
            </Tooltip>
            <Tooltip
              title={t(
                "study.configuration.adequacyPatch.thresholdDisplayLocalMatchingRuleViolations.tooltip",
              )}
            >
              <span>
                <NumberFE
                  label={t(
                    "study.configuration.adequacyPatch.thresholdDisplayLocalMatchingRuleViolations",
                  )}
                  name="thresholdDisplayLocalMatchingRuleViolations"
                  control={control}
                  rules={{
                    validate: validateNumber({ min: 0 }),
                  }}
                />
              </span>
            </Tooltip>
            <Tooltip
              title={t(
                "study.configuration.adequacyPatch.thresholdCsrVariableBoundsRelaxation.tooltip",
              )}
            >
              <span>
                <NumberFE
                  label={t(
                    "study.configuration.adequacyPatch.thresholdCsrVariableBoundsRelaxation",
                  )}
                  name="thresholdCsrVariableBoundsRelaxation"
                  control={control}
                  rules={{
                    validate: validateNumber({
                      min: 0,
                      integer: true,
                    }),
                  }}
                />
              </span>
            </Tooltip>
            {studyVersion >= 930 && (
              <SwitchFE
                label={t("study.configuration.adequacyPatch.redispatch")}
                sx={{ textWrap: "nowrap" }}
                name="redispatch"
                control={control}
              />
            )}
          </Fieldset>
        </>
      )}
    </Box>
  );
}

export default Fields;
