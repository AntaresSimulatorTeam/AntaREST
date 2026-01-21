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
  type AdvancedParamsFormFields,
  type CompatibilityParamsFormFields,
} from "./utils";

function AdvancedParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<AdvancedParamsFormFields> & CompatibilityParamsFormFields) => {
    const { hydroPmax, ...advancedParams } = dirtyValues;
    
    const promises: Promise<unknown>[] = [];
    
    // Update advanced parameters if there are any changes
    if (Object.keys(advancedParams).length > 0) {
      promises.push(setAdvancedParamsFormFields(study.id, advancedParams));
    }
    
    // Update compatibility parameters if hydroPmax changed
    if (hydroPmax !== undefined) {
      promises.push(setCompatibilityParamsFormFields(study.id, { hydroPmax }));
    }
    
    return Promise.all(promises);
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
    <Form
      key={study.id}
      config={{
        defaultValues: async () => {
          const [advancedParams, compatibilityParams] = await Promise.all([
            getAdvancedParamsFormFields(study.id),
            getCompatibilityParamsFormFields(study.id),
          ]);

          return {
            ...advancedParams,
            ...compatibilityParams,
          };
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
