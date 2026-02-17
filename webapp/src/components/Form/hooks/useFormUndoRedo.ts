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

import useUpdatedRef from "@/hooks/useUpdatedRef";
import * as R from "ramda";
import { useCallback, useEffect, useRef } from "react";
import type { FieldValues, Path, UseFormReturn } from "react-hook-form";
import useUndo, { type Actions } from "use-undo";
import useFormInitialDefaultValues from "./useFormInitialDefaultValues";

enum ActionType {
  Undo = "UNDO",
  Redo = "REDO",
  Set = "SET",
}

function useFormUndoRedo<TFieldValues extends FieldValues, TContext>(
  formApi: UseFormReturn<TFieldValues, TContext>,
): Actions<TFieldValues> {
  const [state, { undo, redo, set, ...rest }] = useUndo<TFieldValues | undefined>(undefined);
  const getInitialDefaultValues = useFormInitialDefaultValues(formApi);
  const lastAction = useRef<ActionType | "">("");
  const dataRef = useUpdatedRef({ state, getInitialDefaultValues });

  useEffect(
    () => {
      if (lastAction.current === ActionType.Undo || lastAction.current === ActionType.Redo) {
        const newValues = state.present || getInitialDefaultValues();

        if (newValues) {
          Object.entries(newValues).forEach(([name, value]) => {
            formApi.setValue(name as Path<TFieldValues>, value, { shouldDirty: true });
          });
        }
      }

      lastAction.current = "";
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [state.present],
  );

  const undoWrapper = useCallback(() => {
    undo();
    lastAction.current = ActionType.Undo;
  }, [undo]);

  const redoWrapper = useCallback(() => {
    redo();
    lastAction.current = ActionType.Redo;
  }, [redo]);

  const setWrapper = useCallback<Actions<TFieldValues>["set"]>(
    (newPresent, checkpoint) => {
      const currentPresent =
        dataRef.current.state.present || dataRef.current.getInitialDefaultValues();

      // Don't set after an undo or redo without changes.
      // * Don't use shallow equality, because it can be a deep object.
      if (R.equals(currentPresent, newPresent)) {
        return;
      }

      set(newPresent, checkpoint);
      lastAction.current = ActionType.Set;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [set],
  );

  return {
    ...rest,
    undo: undoWrapper,
    redo: redoWrapper,
    set: setWrapper,
  };
}

export default useFormUndoRedo;
