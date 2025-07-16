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

import { useState } from "react";
import { useAsync } from "react-use";
import type { StudyMetadata } from "../../types/types";
import type { AppState } from "../ducks";
import { createStudySynthesis } from "../ducks/studySyntheses";
import useAppDispatch from "./useAppDispatch";
import useAppSelector from "./useAppSelector";
import { getStudySynthesis } from "../selectors";
import { PromiseStatus, type TPromiseStatus } from "../../hooks/usePromise";
import type { Response } from "../../components/common/utils/UsePromiseCond";

export interface UseStudySynthesisProps<T> {
  studyId: StudyMetadata["id"];
  selector?: (state: AppState, studyId: StudyMetadata["id"]) => T;
}

export default function useStudySynthesis<T>(props: UseStudySynthesisProps<T>): Response<T> {
  const { studyId, selector } = props;
  const isSynthesisExist = useAppSelector((state) => !!getStudySynthesis(state, studyId));
  const data = useAppSelector((state) =>
    isSynthesisExist && selector ? selector(state, studyId) : undefined,
  );
  const dispatch = useAppDispatch();
  const [status, setStatus] = useState<TPromiseStatus>(PromiseStatus.Idle);
  const [error, setError] = useState<Response["error"]>();

  useAsync(async () => {
    if (!isSynthesisExist) {
      setStatus(PromiseStatus.Pending);

      try {
        await dispatch(createStudySynthesis(studyId)).unwrap();
      } catch (e) {
        setError(e as Error);
        setStatus(PromiseStatus.Rejected);
      }
    } else {
      setStatus(PromiseStatus.Fulfilled);
    }
  }, [dispatch, isSynthesisExist, studyId]);

  return { data, status, error };
}
