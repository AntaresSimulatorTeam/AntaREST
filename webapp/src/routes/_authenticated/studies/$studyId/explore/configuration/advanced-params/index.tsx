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
import ViewWrapper from "@/components/page/ViewWrapper";
import { updateStudySynthesis } from "@/redux/ducks/studySyntheses";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { createFileRoute } from "@tanstack/react-router";
import semver from "semver";
import Fields from "./-components/Fields";
import {
  getAdvancedParamsFormFields,
  getCompatibilityParamsFormFields,
  setAdvancedParamsFormFields,
  setCompatibilityParamsFormFields,
  type AdvancedParamsFormFields,
  type CompatibilityParamsFormFields,
} from "./-utils";
import useStudy from "../../../-hooks/useStudy";

/** Form holds advanced params + compatibility (hydroPmax) at runtime. */
type FormValues = AdvancedParamsFormFields & Partial<CompatibilityParamsFormFields>;

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/configuration/advanced-params/",
)({
  component: AdvancedParameters,
});

function AdvancedParameters() {
  const { studyId } = Route.useParams();
  const study = useStudy();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<FormValues>) => {
    const { hydroPmax, ...advancedRest } = dirtyValues;
    const promises: Array<Promise<unknown>> = [setAdvancedParamsFormFields(studyId, advancedRest)];
    if (hydroPmax !== undefined) {
      promises.push(setCompatibilityParamsFormFields(studyId, { hydroPmax }));
    }
    return Promise.all(promises);
  };

  const handleSubmitSuccessful = ({
    dirtyValues: { renewableGenerationModelling },
  }: SubmitHandlerPlus<FormValues>) => {
    if (renewableGenerationModelling) {
      dispatch(
        updateStudySynthesis({
          id: studyId,
          changes: { enr_modelling: renewableGenerationModelling },
        }),
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <Form
        config={{
          defaultValues: async () => {
            const [advanced, compatibility] = await Promise.all([
              getAdvancedParamsFormFields(studyId),
              semver.gte(study.version, "9.2.0")
                ? getCompatibilityParamsFormFields(studyId).catch(() => ({ hydroPmax: undefined }))
                : Promise.resolve({ hydroPmax: undefined }),
            ]);
            return { ...advanced, ...compatibility };
          },
        }}
        onSubmit={handleSubmit}
        onSubmitSuccessful={handleSubmitSuccessful}
        enableUndoRedo
      >
        <Fields />
      </Form>
    </ViewWrapper>
  );
}
