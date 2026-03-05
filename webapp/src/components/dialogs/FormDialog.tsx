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

// `any` is intentional for TContext and SubmitReturnValue defaults: these types are meant to be
// inferred at the call site. Using `unknown` would force every consumer that extends
// FormDialogProps to explicitly specify both type arguments even when they don't care about them.
/* eslint-disable @typescript-eslint/no-explicit-any */
import SaveIcon from "@mui/icons-material/Save";
import { Button } from "@mui/material";
import * as RA from "ramda-adjunct";
import { useId, useState } from "react";
import type { FieldValues, FormState } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { mergeSxProp } from "@/utils/muiUtils";
import Form, { type FormProps } from "../Form";
import BasicDialog, { type BasicDialogProps } from "./BasicDialog";

type SuperType<TFieldValues extends FieldValues, TContext, SubmitReturnValue> = Omit<
  BasicDialogProps,
  "onSubmit" | "onInvalid" | "children"
> &
  Omit<FormProps<TFieldValues, TContext, SubmitReturnValue>, "hideSubmitButton">;

export interface FormDialogProps<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any,
  SubmitReturnValue = any,
> extends SuperType<TFieldValues, TContext, SubmitReturnValue> {
  cancelButtonText?: string;
  onCancel: VoidFunction;
}

function FormDialog<TFieldValues extends FieldValues, TContext, SubmitReturnValue>({
  config,
  onSubmit,
  onSubmitSuccessful,
  onInvalid,
  children,
  onStateChange,
  onCancel,
  onClose,
  cancelButtonText,
  submitButtonText,
  submitButtonIcon,
  allowSubmitOnPristine = false,
  ...dialogProps
}: FormDialogProps<TFieldValues, TContext, SubmitReturnValue>) {
  const formProps = {
    config,
    onSubmit,
    onSubmitSuccessful,
    onInvalid,
    children,
  };

  const { t } = useTranslation();
  const formId = useId();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitAllowed, setIsSubmitAllowed] = useState(allowSubmitOnPristine);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFormStateChange = (formState: FormState<TFieldValues>) => {
    const { isSubmitting, isDirty, disabled: isDisabled } = formState;
    onStateChange?.(formState);
    setIsSubmitting(isSubmitting);
    setIsSubmitAllowed((isDirty || allowSubmitOnPristine) && !isSubmitting && !isDisabled);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const handleClose: FormDialogProps["onClose"] = (...args) => {
    if (!isSubmitting) {
      onCancel();
      onClose?.(...args);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      maxWidth="xs"
      fullWidth
      {...dialogProps}
      contentProps={{
        ...dialogProps.contentProps,
        sx: mergeSxProp({ px: 2 }, dialogProps.contentProps?.sx),
      }}
      onClose={handleClose}
      actions={
        <>
          <Button onClick={onCancel} disabled={isSubmitting}>
            {cancelButtonText || t("global.cancel")}
          </Button>
          <Button
            type="submit"
            form={formId}
            variant="contained"
            disabled={!isSubmitAllowed}
            loading={isSubmitting}
            loadingPosition="start"
            startIcon={RA.isNotUndefined(submitButtonIcon) ? submitButtonIcon : <SaveIcon />}
          >
            {submitButtonText || t("global.save")}
          </Button>
        </>
      }
    >
      <Form
        {...formProps}
        sx={{
          ".Form__Content": {
            p: 1, // Prevent content from touching scrollbar
          },
        }}
        id={formId}
        onStateChange={handleFormStateChange}
        hideSubmitButton
      />
    </BasicDialog>
  );
}

export default FormDialog;
