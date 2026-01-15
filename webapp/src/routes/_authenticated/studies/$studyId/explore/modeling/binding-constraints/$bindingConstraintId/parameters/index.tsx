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

import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";

import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import {
  getBindingConstraint,
  updateBindingConstraint,
} from "@/services/api/studies/bindingConstraints";
import type { BindingConstraint } from "@/services/api/studies/bindingConstraints/type";
import { unresolvedPromise } from "@/utils/promiseUtils";
import { validateString } from "@/utils/validation/string";
import { Stack } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import useBindingConstraint from "../-hooks/useBindingConstraint";
import { OPERATOR_OPTIONS, OUTPUT_FILTERS_OPTIONS, TIME_STEPS_OPTIONS } from "../../-utils";
import TermsFE from "./-components/TermsFE";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/binding-constraints/$bindingConstraintId/parameters/",
)({
  component: Parameters,
});

function Parameters() {
  const study = useStudy();
  const constraint = useBindingConstraint();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<BindingConstraint>) => {
    const { id, name, ...updatedConstraint } = values;

    return updateBindingConstraint({
      studyId: study.id,
      constraintId: constraint.id,
      values: updatedConstraint,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Form
        key={constraint.id}
        config={{
          defaultValues: () =>
            constraint.isOptimistic
              ? unresolvedPromise<BindingConstraint>()
              : getBindingConstraint({ studyId: study.id, constraintId: constraint.id }),
        }}
        onSubmit={handleSubmit}
        enableUndoRedo
      >
        {({ control }) => (
          <Stack direction="column" sx={{ height: 1 }}>
            <Fieldset>
              <SwitchFE
                name="enabled"
                label={t("study.modeling.bindingConst.enabled")}
                control={control}
              />
              <StringFE disabled name="name" label={t("global.name")} control={control} />
              {semver.gte(study.version, "8.7.0") && (
                <StringFE
                  name="group"
                  label={t("global.group")}
                  control={control}
                  rules={{
                    validate: (v) => {
                      if (typeof v === "string") {
                        return validateString(v, {
                          maxLength: 20,
                          specialChars: "-",
                        });
                      }
                    },
                  }}
                />
              )}
              <SelectFE
                name="timeStep"
                label={t("study.modeling.bindingConst.type")}
                options={TIME_STEPS_OPTIONS}
                control={control}
              />
              <SelectFE
                name="operator"
                label={t("study.modeling.bindingConst.operator")}
                options={OPERATOR_OPTIONS}
                control={control}
              />
              <Fieldset.Break />
              {semver.gte(study.version, "8.3.0") && (
                <>
                  <SelectFE
                    name="filterYearByYear"
                    label={t("study.outputFilters.filterByYear")}
                    options={OUTPUT_FILTERS_OPTIONS}
                    multiple
                    control={control}
                    sx={{
                      width: "auto !important",
                      minWidth: 200,
                    }}
                  />
                  <SelectFE
                    name="filterSynthesis"
                    label={t("study.outputFilters.filterSynthesis")}
                    options={OUTPUT_FILTERS_OPTIONS}
                    multiple
                    control={control}
                    sx={{
                      width: "auto !important",
                      minWidth: 200,
                    }}
                  />
                </>
              )}
              <StringFE
                name="comments"
                label={t("study.modeling.bindingConst.comments")}
                control={control}
              />
            </Fieldset>
            <TermsFE />
          </Stack>
        )}
      </Form>
    </>
  );
}
