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
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import ViewWrapper from "@/components/page/ViewWrapper";
import { validateNumber } from "@/utils/validation/number";
import { Tooltip } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import useStudy from "../../../../-hooks/useStudy";
import {
  getAdequacyPatchFormFields,
  PRICE_TAKING_ORDER_OPTIONS,
  setAdequacyPatchFormFields,
  type AdequacyPatchFormFields,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/configuration/adequacy-patch/general/",
)({
  component: General,
});

function General() {
  const { t } = useTranslation();
  const study = useStudy();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<AdequacyPatchFormFields>) => {
    return setAdequacyPatchFormFields(study.id, data.dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <Form
        config={{
          defaultValues: () => getAdequacyPatchFormFields(study.id),
        }}
        onSubmit={handleSubmit}
        enableUndoRedo
      >
        {({ control }) => (
          <>
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
            {semver.gte(study.version, "8.5.0") && (
              <>
                <Fieldset
                  legend={
                    <Tooltip
                      title={t(
                        "study.configuration.adequacyPatch.legend.curtailmentSharing.tooltip",
                        {
                          defaultValue: "",
                        },
                      )}
                    >
                      <span>
                        {t("study.configuration.adequacyPatch.legend.curtailmentSharing")}
                      </span>
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
                  {semver.gte(study.version, "9.3.0") && (
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
          </>
        )}
      </Form>
    </ViewWrapper>
  );
}
