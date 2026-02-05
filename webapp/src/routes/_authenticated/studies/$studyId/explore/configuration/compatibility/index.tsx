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
import SelectFE from "@/components/fieldEditors/SelectFE";
import Fieldset from "@/components/Fieldset";
import ViewWrapper from "@/components/page/ViewWrapper";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import {
  getCompatibilityParamsFormFields,
  setCompatibilityParamsFormFields,
  HYDRO_PMAX_OPTIONS,
} from "./-utils";
import { checkRouteAvailability } from "@/utils/routerUtils";
import useStudy from "../../../-hooks/useStudy";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/configuration/compatibility/",
)({
  component: Compatibility,
});

function Compatibility() {
  const { studyId } = Route.useParams();
  const [t] = useTranslation();
  const study = useStudy();

  checkRouteAvailability({
    studyVersion: study.version,
    minVersion: "9.2.0",
    routePath: Route.path,
  });

  return (
    <ViewWrapper>
      <Form
        config={{
          defaultValues: () => getCompatibilityParamsFormFields(studyId),
        }}
        onSubmit={({ dirtyValues }) => setCompatibilityParamsFormFields(studyId, dirtyValues)}
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
          </Fieldset>
        )}
      </Form>
    </ViewWrapper>
  );
}
