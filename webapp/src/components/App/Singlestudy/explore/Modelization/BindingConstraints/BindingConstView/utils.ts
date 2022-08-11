import { FieldValues } from "react-hook-form";
import {
  ClusterElement,
  LinkCreationInfoDTO,
} from "../../../../../../../common/types";
import { getBindingConstraint } from "../../../../../../../services/api/studydata";

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
  time_step: FilteringType;
  operator: OperatorType;
  comments?: string;
  constraints: Array<ConstraintType>;
}

export type BindingConstFields = BindingConstType;

export type BindingConstPath = Record<keyof BindingConstFields, string>;

export async function getDefaultValues(
  studyId: string,
  bindingConstId: string
): Promise<BindingConstFields> {
  // Fetch fields
  const fields: BindingConstType = await getBindingConstraint(
    studyId,
    bindingConstId
  );
  return fields;
}

export default {};
