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

import FormDialog from "@/components/dialogs/FormDialog";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { validateString } from "@/utils/validation/string";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
// @ts-expect-error Temporary fix for missing lib
import { useOutletContext } from "react-router";
import semver from "semver";
import {
  BindingConstraintOperator,
  TimeStep,
} from "../../../-components/NavHeader/CommandsDrawer/EditionView/commandTypes";
import { setCurrentBindingConst } from "../../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import { createBindingConstraint } from "../../../../../../../services/api/studydata";
import type { StudyMetadata } from "../../../../../../../types/types";
import { type BindingConstraint, OPERATOR_OPTIONS, TIME_STEPS_OPTIONS } from "./utils";

interface Props {
  open: boolean;
  onClose: VoidFunction;
  existingConstraints: Array<BindingConstraint["id"]>;
  reloadConstraintsList: VoidFunction;
}

function AddConstraintDialog({ open, onClose, existingConstraints, reloadConstraintsList }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const [t] = useTranslation();

  const defaultValues = {
    name: "",
    group: semver.gte(study.version, "8.7.0") ? "default" : undefined,
    enabled: true,
    timeStep: TimeStep.HOURLY,
    operator: BindingConstraintOperator.LESS,
    comments: "",
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<typeof defaultValues>) => {
    return createBindingConstraint(study.id, values);
  };

  const handleSubmitSuccessful = (
    _data: SubmitHandlerPlus<typeof defaultValues>,
    createdConstraint: BindingConstraint,
  ) => {
    /**
     * !WARNING: Current Implementation Issues & Future Directions
     *
     * Issues Identified:
     * 1. State vs. Router: Utilizes global state for navigation-related concerns better suited for URL routing, reducing shareability and persistence.
     * 2. Full List Reload: Inefficiently reloads the entire list after adding an item, leading to unnecessary network use and performance hits.
     * 3. Global State Overuse: Over-relies on global state for operations that could be localized, complicating the application unnecessarily.
     *
     * Future Solutions:
     * - React Router Integration: Leverage URL parameters for selecting and displaying binding constraints, improving UX and state persistence.
     * - React Query for State Management: Utilize React Query for data fetching and state management. This introduces benefits like:
     *    - Automatic Revalidation: Only fetches data when needed, reducing unnecessary network requests.
     *    - Optimistic Updates: Immediately reflect changes in the UI while the backend processes the request, enhancing perceived performance.
     *    - Cache Management: Efficiently manage and invalidate cache, ensuring data consistency without manual reloads.
     * - Efficient State Updates: Post-creation, append the new item to the existing list or use React Query's mutation to update the list optimally.
     *
     * Adopting these strategies will significantly enhance efficiency, maintainability, and UX, addressing current architectural weaknesses.
     */
    reloadConstraintsList();
    dispatch(setCurrentBindingConst(createdConstraint.id));
    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      key={study.id}
      title={t("study.modeling.bindingConst.newBindingConst")}
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
      onCancel={onClose}
      open={open}
    >
      {({ control }) => (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
          }}
        >
          <SwitchFE
            name="enabled"
            label={t("study.modeling.bindingConst.enabled")}
            control={control}
          />
          <StringFE
            name="name"
            label={t("global.name")}
            control={control}
            rules={{
              validate: (v) =>
                validateString(v, {
                  existingValues: existingConstraints,
                  specialChars: "@&_-()",
                }),
            }}
          />
          {semver.gte(study.version, "8.7.0") && (
            <StringFE
              name="group"
              label={t("global.group")}
              control={control}
              rules={{
                validate: (v) => {
                  if (typeof v === "string") {
                    return validateString(v, {
                      maxLength: 20,
                      specialChars: "-",
                    });
                  }
                },
              }}
            />
          )}
          <StringFE
            name="comments"
            label={t("study.modeling.bindingConst.comments")}
            control={control}
          />
          <SelectFE
            name="timeStep"
            label={t("study.modeling.bindingConst.type")}
            variant="outlined"
            options={TIME_STEPS_OPTIONS}
            control={control}
          />
          <SelectFE
            name="operator"
            label={t("study.modeling.bindingConst.operator")}
            variant="outlined"
            options={OPERATOR_OPTIONS}
            control={control}
          />
        </Box>
      )}
    </FormDialog>
  );
}

export default AddConstraintDialog;
