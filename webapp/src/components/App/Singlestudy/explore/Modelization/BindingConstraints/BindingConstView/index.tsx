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

import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../../types/types";
import TabsView from "../../../../../../common/TabsView";
import ConstraintForm from "./ConstraintForm";
import ConstraintMatrix from "./ConstraintMatrix";

interface Props {
  constraintId: string;
  reloadConstraintsList: VoidFunction;
}

function BindingConstView({ constraintId, reloadConstraintsList }: Props) {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      divider
      items={[
        {
          label: t("global.parameters"),
          content: (
            <ConstraintForm
              study={study}
              constraintId={constraintId}
              reloadConstraintsList={reloadConstraintsList}
            />
          ),
        },
        {
          label: t("global.timeSeries"),
          content: (
            // Force a remount of ConstraintMatrix when `constraintId` changes.
            // This avoids stale data from `usePromise` that keep returning previous results.
            <ConstraintMatrix key={constraintId} study={study} constraintId={constraintId} />
          ),
        },
      ]}
    />
  );
}

export default BindingConstView;
