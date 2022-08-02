import { FieldValues } from "react-hook-form";
import { LinkCreationInfoDTO } from "../../../../../../../common/types";
import { getStudyData } from "../../../../../../../services/api/study";

type OperatorType = "less" | "equal" | "greater" | "both";
type FilteringType = "hourly" | "daily" | "weekly";

export interface ConstraintType {
  id: string;
  weight: number;
  offset?: number;
  data:
    | LinkCreationInfoDTO
    | {
        area: string;
        cluster: string;
      };
}

export interface BindingConstType extends FieldValues {
  name: string;
  id: string;
  enabled: boolean;
  type: FilteringType;
  operator: OperatorType;
  comments?: string;
  constraints: {
    [elm: string]: ConstraintType;
  };
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

export function getContraintsValues(values: Partial<BindingConstFields>): any {
  const { constraints } = values;
  return constraints;
}

export function parseConstraints(key: string, value: string): ConstraintType {
  const data: ConstraintType = {
    id: key,
    weight: 0,
    // type: "link",
    data: {
      area: "",
      cluster: "",
    },
  };
  const linkTab = key.split("%");
  if (linkTab.length === 2) {
    data.data = {
      area1: linkTab[0],
      area2: linkTab[1],
    };
  } else {
    const clusterTab = key.split(".");
    if (clusterTab.length === 2) {
      // data.type = "cluster";
      data.data = {
        area: clusterTab[0],
        cluster: clusterTab[1],
      };
    }
  }

  try {
    const weight = parseFloat(value as string);
    data.weight = weight;
  } catch (e) {
    if (typeof value === "string") {
      const values = value.split("%");
      if (values.length === 2) {
        // eslint-disable-next-line prefer-destructuring
        data.weight = parseFloat(values[0]);
        // eslint-disable-next-line prefer-destructuring
        data.offset = parseInt(values[1], 10);
      }
    }
  }
  return data;
}

export default {};
