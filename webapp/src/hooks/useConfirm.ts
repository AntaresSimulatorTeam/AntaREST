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

import { useCallback, useRef, useState } from "react";
import useAutoUpdateRef from "./useUpdatedRef";

function errorFunction() {
  throw new Error("Promise is not pending.");
}

/**
 * Hook that allows to wait for a confirmation from the user with a `Promise`.
 * It is intended to be used in conjunction with a confirm view (like `ConfirmationDialog`).
 *
 * @example
 * ```tsx
 * const action = useConfirm();
 *
 * return (
 *   <>
 *     <Button
 *       onClick={() => {
 *         action.showConfirm().then((confirm) => {
 *           if (confirm) {
 *             // ...
 *           }
 *         });
 *       }}
 *     >
 *       Action
 *     </Button>
 *     <ConfirmationDialog
 *       open={action.isPending}
 *       onConfirm={action.yes}
 *       onCancel={action.no}
 *     >
 *       Are you sure?
 *     </ConfirmationDialog>
 *   </>
 * );
 * ```
 *
 * @returns An object with the following properties:
 * - `showConfirm`: A function that returns a `Promise` that resolves to `true` if the user confirms,
 *   `false` if the user refuses, and `null` if the user cancel.
 * - `isPending`: A boolean that indicates if the promise is pending.
 * - `yes`: A function that resolves the promise with `true`.
 * - `no`: A function that resolves the promise with `false`.
 * - `cancel`: A function that resolves the promise with `null`.
 */
function useConfirm() {
  const [isPending, setIsPending] = useState(false);
  const isPendingRef = useAutoUpdateRef(isPending);
  const yesRef = useRef<VoidFunction>(errorFunction);
  const noRef = useRef<VoidFunction>(errorFunction);
  const cancelRef = useRef<VoidFunction>(errorFunction);

  const showConfirm = useCallback(() => {
    if (isPendingRef.current) {
      throw new Error("A promise is already pending");
    }

    setIsPending(true);

    return new Promise<boolean | null>((resolve, reject) => {
      yesRef.current = () => {
        resolve(true);
        setIsPending(false);
      };

      noRef.current = () => {
        resolve(false);
        setIsPending(false);
      };

      cancelRef.current = () => {
        resolve(null);
        setIsPending(false);
      };
    });
  }, []);

  return {
    showConfirm,
    isPending,
    yes: yesRef.current,
    no: noRef.current,
    cancel: cancelRef.current,
  };
}

export default useConfirm;
