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
  debounce,
  DebouncedFunc,
  DebouncedFuncLeading,
  DebounceSettings,
  DebounceSettingsLeading,
} from "lodash";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { useEffect, useMemo, useRef } from "react";
import { F } from "ts-toolbelt";

export interface UseDebounceParams extends DebounceSettings {
  wait?: number;
}

type WaitOrParams = number | UseDebounceParams;

const toParams = R.cond<[WaitOrParams | undefined], UseDebounceParams>([
  [RA.isPlainObj, R.identity as () => UseDebounceParams],
  [RA.isNumber, R.objOf("wait") as () => UseDebounceParams],
  [R.T, RA.stubObj],
]);

function useDebounce<T extends F.Function, U extends WaitOrParams>(
  fn: T,
  params?: U,
): U extends DebounceSettingsLeading
  ? DebouncedFuncLeading<T>
  : DebouncedFunc<T> {
  const { wait, ...options } = toParams(params);
  const fnRef = useRef(fn);

  useEffect(() => {
    fnRef.current = fn;
  });

  const debouncedFn = useMemo(
    () => debounce((...args) => fnRef.current(...args), wait, options),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(options), wait],
  );

  useEffect(() => debouncedFn.cancel, [debouncedFn]);

  return debouncedFn;
}

export default useDebounce;
