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

/* eslint-disable @typescript-eslint/no-explicit-any */
import SaveIcon from "@mui/icons-material/Save";
import { Button } from "@mui/material";
import * as RA from "ramda-adjunct";
import { useId, useState } from "react";
import type { FieldValues, FormState } from "react-hook-form";
import { useTranslation } from "react-i18next";
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

// TODO: `formState.isSubmitting` doesn't update when auto submit enabled

function FormDialog<TFieldValues extends FieldValues, TContext, SubmitReturnValue>(
  props: FormDialogProps<TFieldValues, TContext, SubmitReturnValue>,
) {
  const {
    config,
    onSubmit,
    onSubmitSuccessful,
    onInvalid,
    children,
    autoSubmit,
    onStateChange,
    onCancel,
    onClose,
    cancelButtonText,
    submitButtonText,
    submitButtonIcon,
    allowSubmitOnPristine = false,
    ...dialogProps
  } = props;

  const formProps = {
    config,
    onSubmit,
    onSubmitSuccessful,
    onInvalid,
    children,
    autoSubmit,
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
      onClose={handleClose}
      actions={
        <>
          <Button onClick={onCancel} disabled={isSubmitting}>
            {cancelButtonText || t("global.close")}
          </Button>
          {!autoSubmit && (
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
          )}
        </>
      }
    >
      <Form
        {...formProps}
        sx={{
          ".Form__Loader": {
            position: "absolute",
            top: "10px",
            right: "3px",
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
