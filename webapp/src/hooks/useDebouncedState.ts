/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import {
  DebouncedFunc,
  DebouncedFuncLeading,
  DebounceSettingsLeading,
} from "lodash";
import { useState } from "react";
import useDebounce, { UseDebounceParams } from "./useDebounce";

type WaitOrParams = number | UseDebounceParams;

type DebounceFn<S> = (state: S) => void;

type UseDebouncedStateReturn<S, U extends WaitOrParams> = [
  S,
  U extends DebounceSettingsLeading
    ? DebouncedFuncLeading<DebounceFn<S>>
    : DebouncedFunc<DebounceFn<S>>,
];

function useDebouncedState<S, U extends WaitOrParams = WaitOrParams>(
  initialValue: S | (() => S),
  params?: U,
): UseDebouncedStateReturn<S, U> {
  const [state, setState] = useState(initialValue);

  const debounceFn = useDebounce((newState) => {
    setState(newState);
  }, params);

  return [state, debounceFn];
}

export default useDebouncedState;
