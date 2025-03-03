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
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "@/types/types";
import Form from "../../../../../common/Form";
import type { SubmitHandlerPlus } from "../../../../../common/Form/types";
import Fields from "./Fields";
import {
  getAdequacyPatchFormFields,
  setAdequacyPatchFormFields,
  type AdequacyPatchFormFields,
} from "./utils";
import TableMode from "../../../../../common/TableMode";
import TabsView from "../../../../../common/TabsView";

function AdequacyPatch() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<AdequacyPatchFormFields>) => {
    return setAdequacyPatchFormFields(study.id, data.dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      items={[
        {
          label: t("study.configuration.adequacyPatch.tab.general"),
          content: () => (
            <Form
              key={study.id}
              config={{
                defaultValues: () => getAdequacyPatchFormFields(study.id),
              }}
              onSubmit={handleSubmit}
              enableUndoRedo
            >
              <Fields />
            </Form>
          ),
        },
        {
          label: t("study.configuration.adequacyPatch.tab.perimeter"),
          content: () => (
            <TableMode studyId={study.id} type="areas" columns={["adequacyPatchMode"]} />
          ),
        },
      ]}
    />
  );
}

export default AdequacyPatch;
