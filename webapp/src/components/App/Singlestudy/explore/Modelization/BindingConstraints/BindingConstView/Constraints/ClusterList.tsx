import { useState } from "react";
import { useTranslation } from "react-i18next";
import { GenericInfo } from "../../../../../../../../common/types";
import SelectSingle from "../../../../../../../common/SelectSingle";

export default function ClusterList() {
  const [t] = useTranslation();

  const [area, setArea] = useState("");
  const [cluster, setCluster] = useState("");

  const areas: Array<GenericInfo> = [];
  const clusters: Array<GenericInfo> = [];

  const handleAreaSelection = (value: string) => {
    console.log("AREA: ", value);
    setArea(value);
  };

  const handleClusterSelection = (value: string) => {
    console.log("CLUSTER: ", value);
    setCluster(value);
  };
  return (
    <>
      <SelectSingle
        name={t("study.publicMode")}
        list={areas}
        data={area}
        setValue={(value: string) => handleAreaSelection(value as string)}
        sx={{ flexGrow: 1, height: "60px" }}
      />
      <SelectSingle
        name={t("study.publicMode")}
        list={clusters}
        data={cluster}
        setValue={(value: string) => handleClusterSelection(value as string)}
        sx={{ flexGrow: 1, mx: 1, height: "60px" }}
      />
    </>
  );
}
