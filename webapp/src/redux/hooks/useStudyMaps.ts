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
import type { StudyMetadata } from "../../types/types";
import type { AppState } from "../ducks";
import useAppDispatch from "./useAppDispatch";
import useAppSelector from "./useAppSelector";
import { getStudyMap } from "../selectors";
import { createStudyMap, fetchStudyMapLayers, fetchStudyMapDistricts } from "../ducks/studyMaps";
import useStudySynthesis from "./useStudySynthesis";
import type { Response } from "../../components/common/utils/UsePromiseCond";
import usePromise, { PromiseStatus, type TPromiseStatus } from "../../hooks/usePromise";

interface Props<T> {
  studyId: StudyMetadata["id"];
  selector: (state: AppState, studyId: StudyMetadata["id"]) => T;
}

export default function useStudyMaps<T>({ studyId, selector }: Props<T>): Response<T> {
  const [status, setStatus] = useState<TPromiseStatus>(PromiseStatus.Idle);
  const [error, setError] = useState<Response["error"]>();
  const dispatch = useAppDispatch();
  const synthesis = useStudySynthesis({ studyId });
  const isMapsExists = useAppSelector((state) => !!getStudyMap(state, studyId));
  const data = useAppSelector((state) => selector(state, studyId) || undefined);
  const prevStudyId = useAppSelector((state) => state.studies.prevStudyId);

  usePromise(async () => {
    if (synthesis.status === PromiseStatus.Rejected) {
      setError(synthesis.error);
      setStatus(PromiseStatus.Rejected);
      return;
    }

    if (synthesis.status !== PromiseStatus.Fulfilled) {
      setStatus(PromiseStatus.Pending);
      return;
    }

    setStatus(PromiseStatus.Pending);

    try {
      /*
       * Conditionally fetch study map data to address two scenarios:
       * 1. The map data does not exist for the current study (isMapsExist is false).
       * 2. The user has navigated to a different study than previously viewed (prevStudyId !== studyId).
       *
       * Particularly critical for accuracy when users return to a previously viewed study.
       */
      if (!isMapsExists || prevStudyId !== studyId) {
        await Promise.all([
          dispatch(fetchStudyMapLayers(studyId)).unwrap(),
          dispatch(fetchStudyMapDistricts(studyId)).unwrap(),
          dispatch(createStudyMap(studyId)).unwrap(),
        ]);
      }

      setStatus(PromiseStatus.Fulfilled);
    } catch (err) {
      setError(err as Error);
      setStatus(PromiseStatus.Rejected);
    }
  }, [isMapsExists, studyId, synthesis.status]);

  return { data, status, error };
}
