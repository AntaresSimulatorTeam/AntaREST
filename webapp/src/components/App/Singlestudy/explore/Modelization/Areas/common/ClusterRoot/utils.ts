import * as R from "ramda";
import { FieldValues } from "react-hook-form";
import { Cluster } from "../../../../../../../../common/types";

export interface ClusterElement {
  id: Cluster["id"];
  name: string;
  group: string;
}

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
