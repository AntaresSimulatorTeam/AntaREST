import { useEffect, useState } from "react";
import { StudyMetadata } from "../../common/types";
import { AppState } from "../ducks";
import { createStudySynthesis } from "../ducks/studySyntheses";
import useAppDispatch from "./useAppDispatch";
import useAppSelector from "./useAppSelector";
import { getStudySynthesis } from "../selectors";

interface Props<T> {
  studyId: StudyMetadata["id"];
  selector?: (state: AppState) => T;
}

export default function useStudySynthesis<T>(props: Props<T>): {
  value?: T;
  error?: Error;
  isLoading: boolean;
} {
  const { studyId, selector } = props;
  const isSynthesisExist = useAppSelector(
    (state) => !!getStudySynthesis(state, studyId)
  );
  const value = useAppSelector((state) =>
    isSynthesisExist && selector ? selector(state) : undefined
  );
  const dispatch = useAppDispatch();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error>();

  useEffect(() => {
    if (!isSynthesisExist) {
      try {
        dispatch(createStudySynthesis(studyId)).unwrap();
      } catch (e) {
        setError(e as Error);
      } finally {
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
    }
  }, [dispatch, isSynthesisExist, studyId]);

  return { isLoading, error, value };
}
