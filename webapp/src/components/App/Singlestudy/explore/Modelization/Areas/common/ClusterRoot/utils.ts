import * as R from "ramda";
import { FieldValues } from "react-hook-form";
import { Cluster } from "../../../../../../../../common/types";

export interface ClusterElement {
  id: Cluster["id"];
  name: string;
  group: string;
}

/* name: string;
group: string;
enabled?: boolean; // Default: true
unitcount?: number; // Default: 0
nominalcapacity?: number; // Default: 0
"gen-ts"?: GenTsType; // Default: use global parameter
"min-stable-power"?: number; // Default: 0
"min-down-time"?: number; // Default: 1
"must-run"?: boolean; // Default: false
spinning?: number; // Default: 0
co2?: number; // Default: 0
"volatility.forced"?: number; // Default: 0
"volatility.planned"?: number; // Default: 0
"law.forced"?: LawType; // Default: uniform
"law.planned"?: LawType; // Default: uniform
"marginal-cost"?: number; // Default: 0
"spread-cost"?: number; // Default: 0
"fixed-cost"?: number; // Default: 0
"startup-cost"?: number; // Default: 0
"market-bid-cost"?: number; // Default: 0 */

export type ClusterList = {
  [cluster: string]: ClusterElement;
};

export type Clusters = {
  [group: string]: {
    items: Array<ClusterElement>;
    isOpen: boolean;
  };
};

export interface AddClustersFields extends FieldValues {
  name: string;
  group: string;
}

export const byGroup = R.groupBy((cluster: ClusterElement) => cluster.group);

export default {};
