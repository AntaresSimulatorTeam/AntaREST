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

import usePromise from "@/hooks/usePromise";
import useSafeMemo from "@/hooks/useSafeMemo";
import { login } from "@/redux/ducks/auth";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getAuthUser } from "@/redux/selectors";
import { needAuth } from "@/services/api/auth";
import storage, { StorageKey } from "@/services/utils/localStorage";

function useAuth() {
  const user = useAppSelector(getAuthUser);
  const dispatch = useAppDispatch();

  const { data, isLoading, isRejected } = usePromise(
    async () => {
      if (user) {
        return true;
      }

      if (!(await needAuth())) {
        await dispatch(login());
        return true;
      }

      const userFromStorage = storage.getItem(StorageKey.AuthUser);

      if (userFromStorage) {
        await dispatch(login(userFromStorage));
        return true;
      }

      return false;
    },
    { resetDataOnReload: true, deps: [user, dispatch] },
  );

  const auth = useSafeMemo(
    () => ({ isAuthenticated: data || false, isLoading, isRejected }),
    [data, isLoading, isRejected],
  );

  return auth;
}

export default useAuth;
