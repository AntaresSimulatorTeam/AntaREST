/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useState } from "react";
import * as R from "ramda";
import { useOutletContext } from "react-router";

import { StudyMetadata } from "@/common/types";
import Form from "@/components/common/Form";
import { SubmitHandlerPlus } from "@/components/common/Form/types";

import ScenarioBuilderDialog from "./dialogs/ScenarioBuilderDialog";
import ScenarioPlaylistDialog from "./dialogs/ScenarioPlaylistDialog";
import ThematicTrimmingDialog from "./dialogs/ThematicTrimmingDialog";
import Fields from "./Fields";
import {
  GeneralFormFields,
  getGeneralFormFields,
  hasDayField,
  pickDayFields,
  SetDialogStateType,
  setGeneralFormFields,
} from "./utils";

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
          () => (
            <ThematicTrimmingDialog
              open
              study={study}
              onClose={handleCloseDialog}
            />
          ),
        ],
        [
          R.equals("scenarioBuilder"),
          () => (
            <ScenarioBuilderDialog
              open
              study={study}
              onClose={handleCloseDialog}
            />
          ),
        ],
        [
          R.equals("scenarioPlaylist"),
          () => (
            <ScenarioPlaylistDialog
              open
              study={study}
              onClose={handleCloseDialog}
            />
          ),
        ],
      ])(dialog)}
    </>
  );
}

export default General;
