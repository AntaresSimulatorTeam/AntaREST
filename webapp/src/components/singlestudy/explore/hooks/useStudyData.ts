import { useEffect, useState } from "react";
import {
  FileStudyTreeConfigDTO,
  StudyMetadata,
} from "../../../../common/types";
import { createStudyData } from "../../../../redux/ducks/studyDataSynthesis";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import { getStudyData } from "../../../../redux/selectors";

interface Props<T> {
  studyId: StudyMetadata["id"];
  selector: (state: FileStudyTreeConfigDTO) => T;
}

export default function useStudyData<T>(props: Props<T>): {
  value?: T;
  error?: Error;
  isLoading: boolean;
} {
  const { studyId, selector } = props;
  const isSynthesisExist = useAppSelector(
    (state) => !!getStudyData(state, studyId)
  );
  const value = useAppSelector((state) =>
    isSynthesisExist
      ? selector(getStudyData(state, studyId) as FileStudyTreeConfigDTO)
      : undefined
  );
  const dispatch = useAppDispatch();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error>();

  useEffect(() => {
    if (!isSynthesisExist) {
      try {
        dispatch(createStudyData(studyId)).unwrap();
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
