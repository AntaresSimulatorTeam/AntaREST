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

import * as R from "ramda";
import { UseAsyncEntityStateResponse } from "../hooks/useAsyncAppSelector";
import { FetchStatus } from "../utils";

export interface UseAsyncAppSelectorCondProps<
  Entity,
  Selected,
  Response extends UseAsyncEntityStateResponse<
    Entity,
    Selected
  > = UseAsyncEntityStateResponse<Entity, Selected>,
> {
  response: Response;
  ifLoading?: () => React.ReactNode;
  ifFailed?: (error: Response["error"]) => React.ReactNode;
  ifSucceeded?: (data: Response["value"]) => React.ReactNode;
}

function UseAsyncAppSelectorCond<Entity, Selected>(
  props: UseAsyncAppSelectorCondProps<Entity, Selected>,
) {
  const { response, ifLoading, ifFailed, ifSucceeded } = props;
  const { status, value, error } = response;

  return (
    <>
      {R.cond([
        [
          R.either(R.equals(FetchStatus.Idle), R.equals(FetchStatus.Loading)),
          () => ifLoading?.(),
        ],
        [R.equals(FetchStatus.Failed), () => ifFailed?.(error)],
        [R.equals(FetchStatus.Succeeded), () => ifSucceeded?.(value)],
      ])(status)}
    </>
  );
}

export default UseAsyncAppSelectorCond;
