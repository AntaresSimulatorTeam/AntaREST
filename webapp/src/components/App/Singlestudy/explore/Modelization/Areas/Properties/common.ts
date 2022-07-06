import { result } from "lodash";
import usePromise, {
  PromiseStatus,
} from "../../../../../../../hooks/usePromise";
import { getStudyData } from "../../../../../../../services/api/study";

export interface FieldElement<T = unknown> {
  path?: string;
  value?: T;
}

export interface FieldsInfo {
  [field: string]: FieldElement;
}

// export type Fields<T extends FieldsInfo> = Record<keyof T, string>;
interface ResultType {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data?: any;
  status: PromiseStatus;
  isLoading: boolean;
  error?: string | Error;
}

interface Props<T> {
  fieldsInfo: T;
  studyId: string;
  pathPrefix: string;
}

export function useGetDefaultValues<T extends FieldsInfo>(
  props: Props<T>
): ResultType {
  const { studyId, pathPrefix, fieldsInfo } = props;
  const { data, status, isLoading, error } = usePromise(async () => {
    const fields: T = { ...fieldsInfo };
    await Promise.all(
      Object.keys(fieldsInfo).map(async (item) => {
        const result = await getStudyData(
          studyId,
          `${pathPrefix}/${fieldsInfo[item].path}`
        );
        fields[item].value = result;
      })
    );
    return result;
  });

  return { data, status, isLoading, error };
}

export default {};
