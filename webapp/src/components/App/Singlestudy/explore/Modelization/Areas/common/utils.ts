import * as R from "ramda";
import { FieldValues } from "react-hook-form";
import { Cluster, StudyMetadata } from "../../../../../../../common/types";
import {
  editStudy,
  getStudyData,
} from "../../../../../../../services/api/study";

export async function getDefaultValues<T extends FieldValues>(
  studyId: string,
  area: string,
  cluster: Cluster["id"],
  noDataValues: Partial<T>,
  type: "thermals" | "renewables"
): Promise<T> {
  const pathType = type === "thermals" ? "thermal" : type;
  const pathPrefix = `input/${pathType}/clusters/${area}/list/${cluster}`;
  const data: T = await getStudyData(studyId, pathPrefix, 3);
  Object.keys(noDataValues).forEach((item) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (data as any)[item] =
      data[item] !== undefined ? data[item] : noDataValues[item];
  });
  return data;
}

export const saveField = R.curry(
  <T>(
    studyId: StudyMetadata["id"],
    pathPrefix: string,
    noDataValues: Partial<T>,
    name: string,
    path: string,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    defaultValues: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    data: any
  ): Promise<void> => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (data === (noDataValues as any)[name] || data === undefined) {
      const { [name]: ignore, ...toEdit } = defaultValues;
      let edit = {};
      Object.keys(toEdit).forEach((item) => {
        if (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          toEdit[item] !== (noDataValues as any)[item] &&
          toEdit[item] !== undefined
        ) {
          edit = { ...edit, [item]: toEdit[item] };
        }
      });
      return editStudy(edit, studyId, pathPrefix);
    }
    return editStudy(data, studyId, path);
  }
);
