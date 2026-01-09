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

import FormDialog, { type FormDialogProps } from "@/components/dialogs/FormDialog";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import type { UseFieldArrayAppend } from "react-hook-form";
import useStudySynthesis from "../../../../../../../../../../../../redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "../../../../../../../../../../../../redux/selectors";
import type { AllClustersAndLinks } from "../../../../../../../../../../../../types/types";
import { type BindingConstraint, type ConstraintTerm, isLinkTerm } from "../../../../utils";
import AddConstraintTermForm from "./AddConstraintTermForm";

interface Props extends Omit<FormDialogProps, "children" | "onSubmit"> {
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
  const { onCancel } = dialogProps;

  const linksAndClusters = useStudySynthesis({
    studyId,
    selector: (state) => getLinksAndClusters(state, studyId),
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus) => {
    const newTerm: ConstraintTerm = {
      id: values.id,
      weight: values.weight,
      offset: values.offset,
      data: isLinkTerm(values.data)
        ? { area1: values.data.area1, area2: values.data.area2 }
        : { area: values.data.area, cluster: values.data.cluster },
    };

    append(newTerm);
    onCancel();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog maxWidth="lg" config={{ defaultValues }} onSubmit={handleSubmit} {...dialogProps}>
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
