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

import type { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import type { UseFieldArrayAppend } from "react-hook-form";
import FormDialog, { type FormDialogProps } from "../../../../../../../common/dialogs/FormDialog";
import type { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { isLinkTerm, type BindingConstraint, type ConstraintTerm } from "../utils";
import AddConstraintTermForm from "./AddConstraintTermForm";
import { createConstraintTerm } from "../../../../../../../../services/api/studydata";
import type { AllClustersAndLinks } from "../../../../../../../../types/types";
import useStudySynthesis from "../../../../../../../../redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "../../../../../../../../redux/selectors";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";

interface Props extends Omit<FormDialogProps, "children" | "handleSubmit"> {
  studyId: string;
  constraintId: string;
  append: UseFieldArrayAppend<BindingConstraint, "terms">;
  constraintTerms: ConstraintTerm[];
  options: AllClustersAndLinks;
}

const defaultValues = {
  id: "",
  weight: 0,
  offset: undefined,
  data: {
    area1: "",
    area2: "",
  },
};

/**
 * @deprecated This form and all its children are deprecated due to the original design mixing different
 * types of terms (links and clusters) in a single form state. This approach has proven to be problematic,
 * leading to a non-separate and imprecise form state management. Future development should focus on
 * separating these concerns into distinct components or forms to ensure cleaner, more maintainable code.
 *
 * The current workaround involves conditionally constructing the `newTerm` object based on the term type,
 * which is not ideal and should be avoided in future designs.
 *
 * Potential Future Optimizations:
 * - Separate link and cluster term forms into distinct components to simplify state management and
 *   improve type safety.
 * - Implement more granular type checks or leverage TypeScript discriminated unions more effectively
 *   to avoid runtime type assertions and ensure compile-time type safety.
 * - Consider redesigning the form state structure to more clearly differentiate between link and cluster
 *   terms from the outset, possibly using separate state variables or contexts.
 *
 * Note: This component is not expected to evolve further in its current form. Any necessary bug fixes or
 * minor improvements should be approached with caution, keeping in mind the planned obsolescence.
 *
 * @param props - The props passed to the component.
 * @param  props.studyId - Identifier for the study to which the constraint term is being added.
 * @param  props.constraintId - Identifier for the specific constraint to which the term is added.
 * @param  props.options - Object containing potential options for populating form selects.
 * @param  props.constraintTerms - Array of existing constraint terms.
 * @param  props.append - Function to append the new term to the array of existing terms.
 *
 *@returns A React component that renders the form dialog for adding a constraint term.
 */
function AddConstraintTermDialog({
  studyId,
  constraintId,
  options,
  constraintTerms,
  append,
  ...dialogProps
}: Props) {
  const [t] = useTranslation();
  const { onCancel } = dialogProps;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const linksAndClusters = useStudySynthesis({
    studyId,
    selector: (state) => getLinksAndClusters(state, studyId),
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  /**
   * @deprecated Due to the challenges and limitations associated with dynamically determining term types
   * and constructing term data based on runtime checks, this method is deprecated. Future implementations
   * should consider using separate and explicit handling for different term types to enhance type safety,
   * reduce complexity, and improve code maintainability.
   *
   * Potential future optimizations include adopting separate forms for link and cluster terms, leveraging
   * TypeScript's type system more effectively, and implementing robust form validation.
   *
   * @param root0 - The first parameter object containing all form values.
   * @param root0.values - The structured data of the form, including details about the term being submitted.
   * It includes both link and cluster term fields due to the unified form design.
   * @param _event - The event object for the form submission. May not be
   * used explicitly in the function but is included to match the expected handler signature.
   *
   * @returns A promise that resolves when the term has been successfully submitted
   * and processed or rejects in case of an error.
   */
  const handleSubmit = async (
    { values }: SubmitHandlerPlus<ConstraintTerm>,
    _event?: React.BaseSyntheticEvent,
  ) => {
    try {
      const newTerm = {
        ...values,
        data: isLinkTerm(values.data)
          ? { area1: values.data.area1, area2: values.data.area2 }
          : { area: values.data.area, cluster: values.data.cluster },
      };

      await createConstraintTerm(studyId, constraintId, newTerm);

      append(newTerm);

      enqueueSnackbar(t("study.success.createConstraintTerm"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.createConstraintTerm"), e as AxiosError);
    } finally {
      onCancel();
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      maxWidth="lg"
      config={{ defaultValues }}
      // @ts-expect-error // TODO fix
      onSubmit={handleSubmit}
      {...dialogProps}
    >
      <UsePromiseCond
        response={linksAndClusters}
        ifFulfilled={(data) => (
          <AddConstraintTermForm options={data} constraintTerms={constraintTerms} />
        )}
      />
    </FormDialog>
  );
}

export default AddConstraintTermDialog;
