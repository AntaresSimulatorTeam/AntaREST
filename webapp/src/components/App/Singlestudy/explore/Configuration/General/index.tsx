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
import * as R from "ramda";
import { useState } from "react";
import type { StudyMetadata } from "../../../../../../types/types";
import Form from "../../../../../common/Form";
import Fields from "./Fields";
import ThematicTrimmingDialog from "./dialogs/ThematicTrimmingDialog";
import ScenarioPlaylistDialog from "./dialogs/ScenarioPlaylistDialog";
import {
  getGeneralFormFields,
  hasDayField,
  pickDayFields,
  setGeneralFormFields,
  type GeneralFormFields,
  type SetDialogStateType,
} from "./utils";
import type { SubmitHandlerPlus } from "../../../../../common/Form/types";
import ScenarioBuilderDialog from "./dialogs/ScenarioBuilderDialog";

function General() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [dialog, setDialog] = useState<SetDialogStateType>("");

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

  const handleCloseDialog = () => setDialog("");

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Form
        key={study.id}
        config={{ defaultValues: () => getGeneralFormFields(study.id) }}
        onSubmit={handleSubmit}
        enableUndoRedo
      >
        <Fields setDialog={setDialog} />
      </Form>
      {R.cond([
        [
          R.equals("thematicTrimming"),
          () => <ThematicTrimmingDialog open study={study} onClose={handleCloseDialog} />,
        ],
        [
          R.equals("scenarioBuilder"),
          () => <ScenarioBuilderDialog open study={study} onClose={handleCloseDialog} />,
        ],
        [
          R.equals("scenarioPlaylist"),
          () => <ScenarioPlaylistDialog open study={study} onClose={handleCloseDialog} />,
        ],
      ])(dialog)}
    </>
  );
}

export default General;
