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
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useFormBlocker from "@/hooks/useFormBlocker";
import { toError, voidFn } from "@/utils/fnUtils";
import { mergeSxProp } from "@/utils/muiUtils";
import RedoIcon from "@mui/icons-material/Redo";
import SaveIcon from "@mui/icons-material/Save";
import UndoIcon from "@mui/icons-material/Undo";
import {
  Box,
  Button,
  Divider,
  IconButton,
  setRef,
  Tooltip,
  type ButtonProps,
  type SxProps,
  type Theme,
} from "@mui/material";
import axios from "axios";
import clsx from "clsx";
import * as RA from "ramda-adjunct";
import { useEffect, useRef } from "react";
import {
  FormProvider,
  useForm,
  useFormContext as useFormContextOriginal,
  type FieldValues,
  type FormState,
  type SubmitErrorHandler,
  type UseFormProps,
} from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import CustomScrollbar from "../CustomScrollbar";
import type { SubmitHandlerPlus, UseFormReturnPlus } from "./types";
import useFormApiPlus from "./useFormApiPlus";
import useFormUndoRedo from "./useFormUndoRedo";
import { isMatch, ROOT_ERROR_KEY } from "./utils";

// TODO: Replace built-in validators by Zod (https://react-hook-form.com/docs/useform#resolver).

export interface FormProps<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any,
  SubmitReturnValue = any,
> extends Omit<React.HTMLAttributes<HTMLFormElement>, "onSubmit" | "onInvalid" | "children"> {
  config?: UseFormProps<TFieldValues, TContext>;
  onSubmit?: (
    data: SubmitHandlerPlus<TFieldValues>,
    event?: React.BaseSyntheticEvent,
  ) => void | Promise<SubmitReturnValue>;
  onSubmitSuccessful?: (
    data: SubmitHandlerPlus<TFieldValues>,
    submitResult: SubmitReturnValue,
  ) => void;
  onInvalid?: SubmitErrorHandler<TFieldValues>;
  children:
    | ((formApi: UseFormReturnPlus<TFieldValues, TContext>) => React.ReactNode)
    | React.ReactNode;
  submitButtonText?: string;
  submitButtonIcon?: ButtonProps["startIcon"];
  miniSubmitButton?: boolean;
  hideSubmitButton?: boolean;
  hideFooterDivider?: boolean;
  onStateChange?: (state: FormState<TFieldValues>) => void;
  allowSubmitOnPristine?: boolean;
  enableUndoRedo?: boolean;
  sx?: SxProps<Theme>;
  apiRef?: React.Ref<UseFormReturnPlus<TFieldValues, TContext>>;
  disableStickyFooter?: boolean;
  extraActions?: React.ReactNode | ((state: { canSubmit: boolean }) => React.ReactNode);
  disableBlocker?: boolean;
}

export function useFormContextPlus<TFieldValues extends FieldValues>() {
  return useFormContextOriginal() as UseFormReturnPlus<TFieldValues>;
}

function Form<TFieldValues extends FieldValues, TContext>({
  config,
  onSubmit,
  onSubmitSuccessful,
  onInvalid,
  children,
  submitButtonText,
  submitButtonIcon = <SaveIcon />,
  miniSubmitButton,
  hideSubmitButton,
  hideFooterDivider,
  onStateChange,
  allowSubmitOnPristine = false,
  enableUndoRedo,
  className,
  sx,
  apiRef,
  disableStickyFooter,
  extraActions,
  disableBlocker = false,
  ...formProps
}: FormProps<TFieldValues, TContext>) {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const lastSubmittedData = useRef<TFieldValues>();
  const submitSuccessfulCb = useRef(voidFn);

  const formApi = useForm<TFieldValues, TContext>({
    mode: "onChange",
    delayError: 750,
    ...config,
    defaultValues: RA.isFunction(config?.defaultValues)
      ? () => {
          const fn = config?.defaultValues as () => Promise<TFieldValues>;
          return fn().catch((err) => {
            enqueueErrorSnackbar(t("form.asyncDefaultValues.error"), toError(err));
            throw err;
          });
        }
      : config?.defaultValues,
  });

  const { getValues, setError, handleSubmit, formState, reset } = formApi;

  // * /!\ `formState` is a Proxy
  const { isSubmitting, isSubmitSuccessful, isDirty, disabled: isDisabled, errors } = formState;

  // Don't add `isValid` because we need to trigger fields validation.
  // In case we have invalid default value for example.
  const canSubmit = (isDirty || allowSubmitOnPristine) && !isSubmitting && !isDisabled;
  const rootError = errors.root?.[ROOT_ERROR_KEY];
  const showSubmitButton = !hideSubmitButton;
  const showFooter = showSubmitButton || enableUndoRedo || extraActions || rootError;

  const formApiPlus = useFormApiPlus(formApi);

  const { set: setNewPresent, undo, redo, canUndo, canRedo } = useFormUndoRedo(formApiPlus);

  useFormBlocker({
    isSubmitting,
    // When submit is successful, form still considered dirty until we reset it.
    // So if `isSubmitSuccessful` is true, we consider form not dirty to avoid blocking navigation
    // inside `submitSuccessfulCb.current()`.
    isDirty: isSubmitSuccessful ? false : isDirty,
    disabled: disableBlocker,
  });

  // Reset after successful submit.
  // It's recommended to reset inside useEffect after submission: https://react-hook-form.com/api/useform/reset
  useEffect(
    () => {
      if (isSubmitSuccessful) {
        submitSuccessfulCb.current();

        if (lastSubmittedData.current) {
          // Reset only dirty values make issue with `getValues` and `watch` which only return reset values
          reset(lastSubmittedData.current);

          setNewPresent(lastSubmittedData.current);
        }
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isSubmitSuccessful],
  );

  useUpdateEffect(() => onStateChange?.(formState), [formState]);

  useEffect(() => setRef(apiRef, formApiPlus));

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFormSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    // Prevent parent forms from also submitting if this form is nested
    event.stopPropagation();

    const callback = handleSubmit(async function onValid(data, event) {
      lastSubmittedData.current = data;

      const dirtyValues: Partial<TFieldValues> = getValues(undefined, { dirtyFields: true });
      const dataArg = { values: data, dirtyValues };

      try {
        const submitRes = await onSubmit?.(dataArg, event);

        if (isMatch(submitRes, data)) {
          lastSubmittedData.current = submitRes;
        }

        submitSuccessfulCb.current = () => {
          onSubmitSuccessful?.(dataArg, submitRes);
        };
      } catch (err) {
        enqueueErrorSnackbar(t("form.submit.error"), toError(err));

        // Any error under the `root` key are not persisted with each submission.
        // They will be deleted automatically.
        // cf. https://www.react-hook-form.com/api/useform/seterror/
        setError(`root.${ROOT_ERROR_KEY}`, {
          message: axios.isAxiosError(err) ? err.response?.data.description : err?.toString(),
        });
      }
    }, onInvalid);

    return callback();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      {...formProps}
      sx={mergeSxProp(
        {
          display: "flex",
          flexDirection: "column",
          height: disableStickyFooter ? "auto" : 1,
          overflow: "auto",
        },
        sx,
      )}
      component="form"
      onSubmit={handleFormSubmit}
      className={clsx("Form", className)}
    >
      <Box className="Form__Content" sx={{ overflow: "auto" }}>
        {RA.isFunction(children) ? (
          children(formApiPlus)
        ) : (
          <FormProvider {...formApiPlus}>{children}</FormProvider>
        )}
      </Box>
      {showFooter && (
        <Box
          className="Form__Footer"
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 1.5,
            mt: 1.5,
          }}
        >
          {!hideFooterDivider && <Divider flexItem />}
          {rootError && (
            <Box color="error.main" sx={{ fontSize: "0.9rem" }}>
              {rootError.message || t("form.submit.error")}
            </Box>
          )}
          <CustomScrollbar>
            <Box className="Form__Footer__Actions" sx={{ display: "flex", alignItems: "center" }}>
              {showSubmitButton && (
                <>
                  <Button
                    type="submit"
                    disabled={!canSubmit}
                    loading={isSubmitting}
                    {...(miniSubmitButton
                      ? {
                          children: submitButtonIcon,
                        }
                      : {
                          loadingPosition: "start",
                          startIcon: submitButtonIcon,
                          variant: "contained",
                          children: submitButtonText || t("global.save"),
                        })}
                  />
                  {enableUndoRedo && <Divider sx={{ mx: 2 }} orientation="vertical" flexItem />}
                </>
              )}
              {enableUndoRedo && (
                <>
                  <Tooltip title={t("global.undo")}>
                    <span>
                      <IconButton onClick={undo} disabled={!canUndo || isSubmitting}>
                        <UndoIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                  <Tooltip title={t("global.redo")}>
                    <span>
                      <IconButton onClick={redo} disabled={!canRedo || isSubmitting}>
                        <RedoIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                </>
              )}
              {extraActions && (
                <Box sx={{ ml: "auto", pl: 2, display: "flex", alignItems: "center", gap: 1 }}>
                  {typeof extraActions === "function" ? extraActions({ canSubmit }) : extraActions}
                </Box>
              )}
            </Box>
          </CustomScrollbar>
        </Box>
      )}
    </Box>
  );
}

export default Form;
