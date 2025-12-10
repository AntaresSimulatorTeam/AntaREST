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
import { createFileRoute } from "@tanstack/react-router";
import useStudy from "../../../-hooks/useStudy";
import Fields from "./-components/Fields";
import {
  getGeneralFormFields,
  hasDayField,
  pickDayFields,
  setGeneralFormFields,
  type GeneralFormFields,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/configuration/general/",
)({
  component: General,
});

function General() {
  const study = useStudy();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<GeneralFormFields>) => {
    const { values, dirtyValues } = data;
    const newValues = hasDayField(dirtyValues)
      ? {
          ...dirtyValues,
          // Required by server to validate values
          ...pickDayFields(values),
        }
      : dirtyValues;

    return setGeneralFormFields(study.id, newValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id}
      config={{ defaultValues: () => getGeneralFormFields(study.id) }}
      onSubmit={handleSubmit}
      enableUndoRedo
    >
      <Fields study={study} />
    </Form>
  );
}

export default General;
