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

import TabsView from "@/components/page/TabsView";
import ViewWrapper from "@/components/page/ViewWrapper";
import useDialog from "@/hooks/useDialog";
import { isQueryListItemOptimistic } from "@/queries/utils";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { Delete } from "@mui/icons-material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DeleteIcon from "@mui/icons-material/Delete";
import { Button } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import DuplicateConstraintDialog from "../-components/DuplicateConstraintDialog";
import useDeleteBindingConstraint from "../-hooks/useDeleteBindingConstraint";
import useBindingConstraint from "./-hooks/useBindingConstraint";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/binding-constraints/$bindingConstraintId",
)({
  component: BindingConstraintLayout,
});

function BindingConstraintLayout() {
  const study = useStudy();
  const params = Route.useParams();
  const { t } = useTranslation();
  const { openDialog, confirm } = useDialog();
  const constraint = useBindingConstraint();
  const deleteConstraint = useDeleteBindingConstraint();
  const isOptimistic = isQueryListItemOptimistic(constraint);
  const { bindingConstraintId } = params;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const handleDuplicate = () => {
    openDialog(({ onClose }) => (
      <DuplicateConstraintDialog constraintToDuplicate={constraint} onCancel={onClose} />
    ));
  };

  const handleDelete = async () => {
    const isConfirmed = await confirm({
      content: t("study.modeling.bindingConst.question.deleteBindingConstraint", {
        name: constraint.name,
      }),
      alert: "error",
      titleIcon: DeleteIcon,
    });

    if (isConfirmed) {
      deleteConstraint.mutate({
        studyId: study.id,
        constraintId: bindingConstraintId,
      });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <TabsView
        tabs={[
          {
            id: "parameters",
            label: t("global.parameters"),
            linkOptions: {
              to: "/studies/$studyId/explore/modeling/binding-constraints/$bindingConstraintId/parameters",
              params,
            },
          },
          {
            id: "time-series",
            label: t("global.timeSeries"),
            linkOptions: {
              to: "/studies/$studyId/explore/modeling/binding-constraints/$bindingConstraintId/time-series",
              params,
            },
          },
        ]}
        extraActions={
          <>
            <Button
              variant="outlined"
              startIcon={<ContentCopyIcon />}
              onClick={handleDuplicate}
              disabled={isOptimistic}
            >
              {t("global.duplicate")}
            </Button>
            <Button
              variant="outlined"
              startIcon={<Delete />}
              color="error"
              onClick={handleDelete}
              disabled={isOptimistic}
            >
              {t("global.delete")}
            </Button>
          </>
        }
      />
    </ViewWrapper>
  );
}
