import { useEffect, useState } from "react";
import { useAsync } from "react-use";
import { StudyMetadata } from "../../common/types";
import { AppState } from "../ducks";
import { createStudySynthesis } from "../ducks/studySyntheses";
import useAppDispatch from "./useAppDispatch";
import useAppSelector from "./useAppSelector";
import { getStudySynthesis } from "../selectors";
import { PromiseStatus } from "../../hooks/usePromise";
import { Response } from "../../components/common/utils/UsePromiseCond";

interface Props<T> {
  studyId: StudyMetadata["id"];
  selector?: (state: AppState, studyId: StudyMetadata["id"]) => T;
}

export default function useStudySynthesis<T>(props: Props<T>): Response<T> {
  const { studyId, selector } = props;
  const isSynthesisExist = useAppSelector(
    (state) => !!getStudySynthesis(state, studyId)
  );
  const data = useAppSelector((state) =>
    isSynthesisExist && selector ? selector(state, studyId) : undefined
  );
  const dispatch = useAppDispatch();
  const [status, setStatus] = useState(PromiseStatus.Idle);
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
      setStatus(PromiseStatus.Resolved);
    }
  }, [dispatch, isSynthesisExist, studyId]);

  return { data, status, error };
}
