import { useEffect, useState } from "react";
import { StudyMetadata } from "../../common/types";
import { AppState } from "../ducks";
import useAppDispatch from "./useAppDispatch";
import useAppSelector from "./useAppSelector";
import { getStudyMap } from "../selectors";
import { createStudyMap } from "../ducks/studyMaps";
import useStudySynthesis from "./useStudySynthesis";
import { setCurrentArea } from "../ducks/studySyntheses";
import { Response } from "../../components/common/utils/UsePromiseCond";
import { PromiseStatus } from "../../hooks/usePromise";

interface Props<T> {
  studyId: StudyMetadata["id"];
  selector?: (state: AppState, studyId: StudyMetadata["id"]) => T;
}

export default function useStudyMaps<T>(props: Props<T>): Response<T> {
  const { studyId, selector } = props;
  const synthesisRes = useStudySynthesis({ studyId });
  const isMapsExist = useAppSelector((state) => !!getStudyMap(state, studyId));
  const data = useAppSelector((state) =>
    isMapsExist && selector ? selector(state, studyId) : undefined
  );
  const dispatch = useAppDispatch();
  const [status, setStatus] = useState(PromiseStatus.Idle);
  const [error, setError] = useState<Response["error"]>();

  useEffect(() => {
    if (synthesisRes.status === PromiseStatus.Rejected) {
      setError(synthesisRes.error);
      setStatus(PromiseStatus.Rejected);
    }

    if (synthesisRes.status !== PromiseStatus.Resolved) {
      setStatus(PromiseStatus.Pending);
    }

    if (!isMapsExist) {
      setStatus(PromiseStatus.Pending);

      try {
        // Prevent default selected node on first render
        dispatch(setCurrentArea(""));
        dispatch(createStudyMap(studyId)).unwrap();
      } catch (e) {
        setError(e as Error);
        setStatus(PromiseStatus.Rejected);
      }
    } else {
      setStatus(PromiseStatus.Resolved);
    }
  }, [dispatch, isMapsExist, studyId, synthesisRes]);

  return { data, status, error };
}
