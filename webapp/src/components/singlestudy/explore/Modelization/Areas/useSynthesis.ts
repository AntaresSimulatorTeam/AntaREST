import { useEffect, useState } from "react";
import {
  FileStudyTreeConfigDTO,
  StudyMetadata,
} from "../../../../../common/types";
import { createSynthesis } from "../../../../../redux/ducks/synthesis";
import { useAppDispatch, useAppSelector } from "../../../../../redux/hooks";
import { getSynthesis } from "../../../../../redux/selectors";

interface Props<T> {
  studyId: StudyMetadata["id"];
  selector: (state: FileStudyTreeConfigDTO) => T;
}

export default function useSynthesis<T>(props: Props<T>): {
  value?: T;
  error?: Error;
  isLoading: boolean;
} {
  const { studyId, selector } = props;
  const isSynthesisExist = useAppSelector(
    (state) => !!getSynthesis(state, studyId)
  );
  const value = useAppSelector((state) =>
    isSynthesisExist
      ? selector(getSynthesis(state, studyId) as FileStudyTreeConfigDTO)
      : undefined
  );
  const dispatch = useAppDispatch();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error>();

  useEffect(() => {
    if (!isSynthesisExist) {
      try {
        dispatch(createSynthesis(studyId)).unwrap();
      } catch (e) {
        setError(e as Error);
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
    }
  }, [dispatch, isSynthesisExist, studyId]);

  return { isLoading, error, value };
}
