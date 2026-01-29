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

import { useOutletContext } from "react-router";
import semver from "semver";
import type { StudyMetadata } from "../../../../../../types/types";
import { updateStudySynthesis } from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import Form from "../../../../../common/Form";
import type { SubmitHandlerPlus } from "../../../../../common/Form/types";
import Fields from "./Fields";
import {
  getAdvancedParamsFormFields,
  getCompatibilityParamsFormFields,
  setAdvancedParamsFormFields,
  setCompatibilityParamsFormFields,
  type AdvancedParamsFormFieldsWithCompatibility,
} from "./utils";

function AdvancedParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({
    dirtyValues,
  }: SubmitHandlerPlus<AdvancedParamsFormFieldsWithCompatibility>) => {
    const { hydroPmax, ...advancedRest } = dirtyValues;
    const promises = [setAdvancedParamsFormFields(study.id, advancedRest)];
    if (hydroPmax !== undefined) {
      promises.push(setCompatibilityParamsFormFields(study.id, { hydroPmax }));
    }
    return Promise.all(promises);
  };

  const handleSubmitSuccessful = ({
    dirtyValues: { renewableGenerationModelling },
  }: SubmitHandlerPlus<AdvancedParamsFormFieldsWithCompatibility>) => {
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
    <Form
      key={study.id}
      config={{
        defaultValues: async () => {
          const [advanced, compatibility] = await Promise.all([
            getAdvancedParamsFormFields(study.id),
            semver.gte(study.version, "9.2.0")
              ? getCompatibilityParamsFormFields(study.id)
              : Promise.resolve({}),
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
  );
}

export default AdvancedParameters;
