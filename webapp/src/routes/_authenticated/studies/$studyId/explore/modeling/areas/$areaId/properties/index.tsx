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
import Fields from "./-components/Fields";
import {
  getPropertiesFormFields,
  setPropertiesFormFields,
  type PropertiesFormFields,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/properties/",
)({
  component: Properties,
});

function Properties() {
  const { studyId, areaId } = Route.useParams();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<PropertiesFormFields>) => {
    const { dirtyValues } = data;
    return setPropertiesFormFields(studyId, areaId, dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={areaId}
      config={{
        defaultValues: () => getPropertiesFormFields(studyId, areaId),
      }}
      onSubmit={handleSubmit}
      enableUndoRedo
    >
      <Fields />
    </Form>
  );
}
