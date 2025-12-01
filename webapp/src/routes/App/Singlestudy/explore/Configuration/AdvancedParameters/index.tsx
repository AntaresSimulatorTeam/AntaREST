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

import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../types/types";
import { updateStudySynthesis } from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import Form from "../../../../../common/Form";
import type { SubmitHandlerPlus } from "../../../../../common/Form/types";
import Fields from "./Fields";
import {
  getAdvancedParamsFormFields,
  setAdvancedParamsFormFields,
  type AdvancedParamsFormFields,
} from "./utils";

function AdvancedParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
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
    <Form
      key={study.id}
      config={{
        defaultValues: () => getAdvancedParamsFormFields(study.id),
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
