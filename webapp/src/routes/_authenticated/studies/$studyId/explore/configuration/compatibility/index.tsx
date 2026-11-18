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

import SelectFE from "@/components/fieldEditors/SelectFE";
import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import ViewWrapper from "@/components/page/ViewWrapper";
import { checkRouteAvailability } from "@/utils/routerUtils";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import useStudy from "../../../-hooks/useStudy";
import {
  getCompatibilityParamsFormFields,
  HYDRO_PMAX_OPTIONS,
  HYDRO_RULE_CURVES_OPTIONS,
  setCompatibilityParamsFormFields,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/configuration/compatibility/",
)({
  component: Compatibility,
});

function Compatibility() {
  const [t] = useTranslation();
  const study = useStudy();

  checkRouteAvailability({
    study,
    minVersion: "9.2.0",
    routePath: Route.path,
  });

  return (
    <ViewWrapper>
      <Form
        config={{
          defaultValues: () => getCompatibilityParamsFormFields(study.id),
        }}
        onSubmit={({ dirtyValues }) => setCompatibilityParamsFormFields(study.id, dirtyValues)}
        enableUndoRedo
      >
        {({ control }) => (
          <Fieldset legend={t("study.configuration.compatibility")}>
            <SelectFE
              label={t("study.configuration.compatibility.hydroPmax")}
              options={HYDRO_PMAX_OPTIONS}
              name="hydroPmax"
              control={control}
            />
            {semver.gte(study.version, "10.2.0") && (
              <SelectFE
                label={t("study.configuration.compatibility.hydroRuleCurves")}
                options={HYDRO_RULE_CURVES_OPTIONS}
                name="hydroRuleCurves"
                control={control}
              />
            )}
          </Fieldset>
        )}
      </Form>
    </ViewWrapper>
  );
}
