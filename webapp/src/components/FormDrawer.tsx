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
// FormDrawerProps to explicitly specify both type arguments even when they don't care about them.
/* eslint-disable @typescript-eslint/no-explicit-any */
import CloseIcon from "@mui/icons-material/Close";
import SaveIcon from "@mui/icons-material/Save";
import type { SvgIconComponent } from "@mui/icons-material";
import {
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  Toolbar,
  Tooltip,
  Typography,
  type DrawerProps,
} from "@mui/material";
import * as RA from "ramda-adjunct";
import { useId, useState } from "react";
import type { FieldValues, FormState } from "react-hook-form";
import { useTranslation } from "react-i18next";
import Form, { type FormProps } from "./Form";

type SuperType<TFieldValues extends FieldValues, TContext, SubmitReturnValue> = Omit<
  DrawerProps,
  "onSubmit" | "children" | "title"
> &
  Omit<FormProps<TFieldValues, TContext, SubmitReturnValue>, "hideSubmitButton" | "sx" | "title">;

/**
 * Props for {@link FormDrawer}.
 *
 * Mirrors `FormDialogProps` but for a Drawer: all `Form` props plus the drawer-specific
 * `title`, `titleIcon`, `width` and `anchor`. `onCancel` is required and is called both
 * when the user dismisses the drawer and after a successful submit.
 */
export interface FormDrawerProps<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any,
  SubmitReturnValue = any,
> extends SuperType<TFieldValues, TContext, SubmitReturnValue> {
  title?: React.ReactNode;
  titleIcon?: SvgIconComponent;
  cancelButtonText?: string;
  onCancel: VoidFunction;
  /**
   * Width of the drawer paper.
   *
   * @default 480
   */
  width?: number | string;
}

// Renders a `Form` inside a Drawer with Cancel/Save actions in a sticky footer.
//
// It's the Drawer counterpart of `FormDialog`: a submittable form that can be opened from any
// click event (table row, button, menu item…). The drawer closes automatically after a
// successful submit, and closing is blocked while a submission is in progress.
function FormDrawer<TFieldValues extends FieldValues, TContext, SubmitReturnValue>({
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
  title,
  titleIcon: TitleIcon,
  width = 480,
  anchor = "right",
  ...drawerProps
}: FormDrawerProps<TFieldValues, TContext, SubmitReturnValue>) {
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

  // Close the drawer after a successful submit.
  const handleSubmitSuccessful: FormProps<
    TFieldValues,
    TContext,
    SubmitReturnValue
  >["onSubmitSuccessful"] = (data, submitResult) => {
    onSubmitSuccessful?.(data, submitResult);
    onCancel();
  };

  const handleCancel = () => {
    if (!isSubmitting) {
      onCancel();
    }
  };

  const handleClose: DrawerProps["onClose"] = (...args) => {
    if (!isSubmitting) {
      onCancel();
      onClose?.(...args);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Drawer
      anchor={anchor}
      {...drawerProps}
      onClose={handleClose}
      PaperProps={{ sx: { width, maxWidth: "100%", display: "flex", flexDirection: "column" } }}
    >
      <Toolbar sx={{ flexShrink: 0 }}>
        {TitleIcon && <TitleIcon sx={{ mr: 1 }} />}
        <Typography variant="h6" sx={{ flex: 1 }} noWrap>
          {title}
        </Typography>
        <Tooltip title={cancelButtonText || t("global.close")}>
          <span>
            <IconButton onClick={handleCancel} disabled={isSubmitting} edge="end">
              <CloseIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Toolbar>
      <Divider />
      <Form
        config={config}
        onSubmit={onSubmit}
        onSubmitSuccessful={handleSubmitSuccessful}
        onInvalid={onInvalid}
        id={formId}
        onStateChange={handleFormStateChange}
        sx={{ flex: 1, p: 2 }}
        hideSubmitButton
      >
        {children}
      </Form>
      <Divider />
      <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, p: 1.5, flexShrink: 0 }}>
        <Button onClick={handleCancel} disabled={isSubmitting}>
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
      </Box>
    </Drawer>
  );
}

export default FormDrawer;
