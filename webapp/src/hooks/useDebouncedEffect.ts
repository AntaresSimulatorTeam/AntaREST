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

import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { useEffect } from "react";
import useDebounce, { type UseDebounceParams } from "./useDebounce";

export interface UseDebouncedEffectParams extends UseDebounceParams {
  deps?: React.DependencyList;
}

type DepsOrWaitOrParams = React.DependencyList | number | UseDebouncedEffectParams;

const toParams = R.cond<[DepsOrWaitOrParams | undefined], UseDebouncedEffectParams>([
  [RA.isPlainObj, R.identity as () => UseDebouncedEffectParams],
  [RA.isNumber, R.objOf("wait") as () => UseDebouncedEffectParams],
  [RA.isArray, R.objOf("deps") as () => UseDebouncedEffectParams],
  [R.T, RA.stubObj],
]);

function useDebouncedEffect(effect: VoidFunction, params?: DepsOrWaitOrParams): void {
  const { deps, ...debounceParams } = toParams(params);
  const debouncedFn = useDebounce(effect, debounceParams);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(debouncedFn, deps);
}

export default useDebouncedEffect;
