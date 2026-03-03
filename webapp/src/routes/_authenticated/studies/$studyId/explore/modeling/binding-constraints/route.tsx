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

import EmptyView from "@/components/page/EmptyView";
import RouterListView from "@/components/page/list/RouterListView";
import useDialog from "@/hooks/useDialog";
import { bindingConstraintQueries } from "@/queries/bindingConstraints/queries";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import AddConstraintDialog from "./-components/AddConstraintDialog";
import { bindingConstraintsToList } from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/binding-constraints",
)({
  loader: async ({ context, params: { studyId } }) => {
    await context.queryClient.ensureQueryData(bindingConstraintQueries.list(studyId));
  },
  component: BindingConstraintsLayout,
});

function BindingConstraintsLayout() {
  const { studyId } = Route.useParams();
  const { openDialog } = useDialog();
  const { t } = useTranslation();

  const { data: list } = useSuspenseQuery({
    ...bindingConstraintQueries.list(studyId),
    select: bindingConstraintsToList,
  });

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleAdd = () => {
    openDialog(({ onClose }) => <AddConstraintDialog onCancel={onClose} />);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <RouterListView
      splitId="binding-constraints"
      list={list}
      emptyListView={<EmptyView title={t("study.bindingConstraints.empty")} />}
      onAdd={handleAdd}
    />
  );
}
