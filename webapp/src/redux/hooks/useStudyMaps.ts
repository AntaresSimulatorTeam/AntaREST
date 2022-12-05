import { useEffect, useState } from "react";
import { StudyMetadata } from "../../common/types";
import { AppState } from "../ducks";
import useAppDispatch from "./useAppDispatch";
import useAppSelector from "./useAppSelector";
import { getStudyMap } from "../selectors";
import { createStudyMap } from "../ducks/studyMaps";
import useStudySynthesis from "./useStudySynthesis";
import { setCurrentArea } from "../ducks/studySyntheses";

interface Props<T> {
  studyId: StudyMetadata["id"];
  selector?: (state: AppState) => T;
}

export default function useStudyMaps<T>(props: Props<T>): {
  value?: T;
  error?: Error;
  isLoading: boolean;
} {
  const { studyId, selector } = props;
  const synthesisRes = useStudySynthesis({ studyId });
  const isMapsExist = useAppSelector((state) => !!getStudyMap(state, studyId));
  const value = useAppSelector((state) =>
    isMapsExist && selector ? selector(state) : undefined
  );
  const dispatch = useAppDispatch();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error>();

  useEffect(() => {
    if (synthesisRes.error || synthesisRes.isLoading) {
      return;
    }
    if (!isMapsExist) {
      try {
        // Prevent default selected node on first render
        dispatch(setCurrentArea(""));
        dispatch(createStudyMap(studyId)).unwrap();
      } catch (e) {
        setError(e as Error);
      } finally {
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
    }
  }, [dispatch, isMapsExist, studyId, synthesisRes]);

  return { isLoading, error, value };
}
