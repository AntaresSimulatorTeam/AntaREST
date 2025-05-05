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

import { useMemo } from "react";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import FormDialog from "../../../../../common/dialogs/FormDialog";
import { BindingConstraintOperator, TimeStep } from "../../../Commands/Edition/commandTypes";
import type { SubmitHandlerPlus } from "../../../../../common/Form/types";
import { OPERATORS, TIME_STEPS, type BindingConstraint } from "./BindingConstView/utils";
import { createBindingConstraint } from "../../../../../../services/api/studydata";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";
import type { StudyMetadata } from "../../../../../../types/types";
import { setCurrentBindingConst } from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { useOutletContext } from "react-router";
import { validateString } from "@/utils/validation/string";

interface Props {
  open: boolean;
  onClose: VoidFunction;
  existingConstraints: Array<BindingConstraint["id"]>;
  reloadConstraintsList: VoidFunction;
}

// TODO rename AddConstraintDialog
function AddDialog({ open, onClose, existingConstraints, reloadConstraintsList }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useAppDispatch();
  const [t] = useTranslation();
  const studyVersion = Number(study.version);

  const defaultValues = {
    name: "",
    group: studyVersion >= 870 ? "default" : "",
    enabled: true,
    timeStep: TimeStep.HOURLY,
    operator: BindingConstraintOperator.LESS,
    comments: "",
  };

  const operatorOptions = useMemo(
    () =>
      OPERATORS.map((operator) => ({
        label: t(`study.modelization.bindingConst.operator.${operator}`),
        value: operator,
      })),
    [t],
  );

  const timeStepOptions = useMemo(
    () =>
      TIME_STEPS.map((timeStep) => ({
        label: t(`global.time.${timeStep}`),
        value: timeStep,
      })),
    [t],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<typeof defaultValues>) => {
    return createBindingConstraint(study.id, values);
  };

  const handleSubmitSuccessful = (
    data: SubmitHandlerPlus<typeof defaultValues>,
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
    enqueueSnackbar(t("study.success.addBindingConst"), {
      variant: "success",
    });
    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      key={study.id}
      title={t("study.modelization.bindingConst.newBindingConst")}
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
            label={t("study.modelization.bindingConst.enabled")}
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
          {studyVersion >= 870 && (
            <StringFE
              name="group"
              label={t("global.group")}
              control={control}
              rules={{
                validate: (v) =>
                  validateString(v, {
                    maxLength: 20,
                    specialChars: "-",
                  }),
              }}
            />
          )}
          <StringFE
            name="comments"
            label={t("study.modelization.bindingConst.comments")}
            control={control}
          />
          <SelectFE
            name="timeStep"
            label={t("study.modelization.bindingConst.type")}
            variant="outlined"
            options={timeStepOptions}
            control={control}
          />
          <SelectFE
            name="operator"
            label={t("study.modelization.bindingConst.operator")}
            variant="outlined"
            options={operatorOptions}
            control={control}
          />
        </Box>
      )}
    </FormDialog>
  );
}

export default AddDialog;
