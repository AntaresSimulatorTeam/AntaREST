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

import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import ViewWrapper from "@/components/page/ViewWrapper";
import { updateStudySynthesis } from "@/redux/ducks/studySyntheses";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { createFileRoute } from "@tanstack/react-router";
import useStudy from "../../../-hooks/useStudy";
import Fields from "./-components/Fields";
import {
  getAdvancedParamsFormFields,
  setAdvancedParamsFormFields,
  type AdvancedParamsFormFields,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/configuration/advanced-params/",
)({
  component: AdvancedParameters,
});

function AdvancedParameters() {
  const study = useStudy();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<AdvancedParamsFormFields>) => {
    return setAdvancedParamsFormFields(study.id, dirtyValues);
  };

  const handleSubmitSuccessful = ({
    dirtyValues: { renewableGenerationModelling },
  }: SubmitHandlerPlus<AdvancedParamsFormFields>) => {
    if (renewableGenerationModelling) {
      dispatch(
        updateStudySynthesis({
          id: study.id,
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
          defaultValues: () => getAdvancedParamsFormFields(study.id),
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
