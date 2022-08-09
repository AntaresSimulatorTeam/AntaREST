import { FieldValues } from "react-hook-form";
import {
  ClusterElement,
  LinkCreationInfoDTO,
} from "../../../../../../../common/types";
import { getStudyData } from "../../../../../../../services/api/study";

type OperatorType = "less" | "equal" | "greater" | "both";
type FilteringType = "hourly" | "daily" | "weekly";

export interface ConstraintType {
  id: string;
  weight: number;
  offset?: number;
  data: LinkCreationInfoDTO | ClusterElement;
}

export interface BindingConstType extends FieldValues {
  name: string;
  id: string;
  enabled: boolean;
  type: FilteringType;
  operator: OperatorType;
  comments?: string;
  constraints: Array<ConstraintType>;
}

export type BindingConstFields = Omit<BindingConstType, "id">;

export type BindingConstPath = Omit<
  Record<keyof BindingConstFields, string>,
  "id"
>;

export async function getDefaultValues(
  studyId: string,
  bcIndex: number
): Promise<BindingConstFields> {
  // Path
  const pathPrefix = `input/bindingconstraints/bindingconstraints/${bcIndex}`;
  // Fetch fields
  const fields: BindingConstType = await getStudyData(studyId, pathPrefix, 3);
  return fields;
}

export default {};
