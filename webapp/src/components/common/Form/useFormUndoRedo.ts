/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import useUndo, { Actions } from "use-undo";
import { FieldValues } from "react-hook-form";
import { useCallback, useEffect, useRef } from "react";
import * as R from "ramda";
import { UseFormReturnPlus } from "./types";
import useAutoUpdateRef from "@/hooks/useAutoUpdateRef";

enum ActionType {
  Undo = "UNDO",
  Redo = "REDO",
  Set = "SET",
}

function useFormUndoRedo<TFieldValues extends FieldValues, TContext>(
  api: UseFormReturnPlus<TFieldValues, TContext>,
): Actions<TFieldValues> {
  const {
    setValues,
    _internal: { initialDefaultValues },
  } = api;
  const [state, { undo, redo, set, ...rest }] = useUndo(initialDefaultValues);
  const lastAction = useRef<ActionType | "">("");
  const dataRef = useAutoUpdateRef({ state, initialDefaultValues });

  useEffect(
    () => {
      if (
        lastAction.current === ActionType.Undo ||
        lastAction.current === ActionType.Redo
      ) {
        const newValues = state.present || initialDefaultValues;
        if (newValues) {
          setValues(newValues);
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
        dataRef.current.state.present || dataRef.current.initialDefaultValues;

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
