import * as R from "ramda";
import { FieldValues } from "react-hook-form";

export interface Cluster {
  name: string;
  group: string;
  unitcount: number;
  nominalcapacity: number;
  spinning: number;
  co2: number;
  "marginal-cost": number;
  "market-bid-cost": number;
}

export type ClusterList = {
  [cluster: string]: Cluster;
};

export type Clusters = {
  [group: string]: {
    items: Array<Cluster>;
    isOpen: boolean;
  };
};

export interface AddClustersFields extends FieldValues {
  name: string;
  group: string;
}

export const byGroup = R.groupBy((cluster: Cluster) => cluster.group);

export default {};
