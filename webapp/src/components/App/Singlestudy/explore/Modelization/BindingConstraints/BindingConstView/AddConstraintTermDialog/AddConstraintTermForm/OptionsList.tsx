import { useEffect, useMemo, useState } from "react";
import {
  UseFormSetValue,
  UseFormUnregister,
  UseFormWatch,
} from "react-hook-form";
import { useTranslation } from "react-i18next";
import { AllClustersAndLinks } from "../../../../../../../../../common/types";
import SelectFE from "../../../../../../../../common/fieldEditors/SelectFE";
import { ControlPlus } from "../../../../../../../../common/Form/types";
import {
  BindingConstFields,
  ConstraintType,
  dataToId,
  isTermExist,
} from "../../utils";

interface Props {
  list: AllClustersAndLinks;
  isLink: boolean;
  control: ControlPlus<ConstraintType>;
  watch: UseFormWatch<ConstraintType>;
  constraintsTerm: BindingConstFields["constraints"];
  setValue: UseFormSetValue<ConstraintType>;
  unregister: UseFormUnregister<ConstraintType>;
}

export default function OptionsList(props: Props) {
  const {
    list,
    isLink,
    control,
    constraintsTerm,
    watch,
    setValue,
    unregister,
  } = props;
  const [t] = useTranslation();
  const name1 = isLink ? "area1" : "area";
  const name2 = isLink ? "area2" : "cluster";
  const linksOrClusters = isLink ? list.links : list.clusters;
  const options1 = useMemo(() => {
    return linksOrClusters.map((elm) => ({
      label: elm.element.name,
      value: elm.element.id,
    }));
  }, [linksOrClusters]);

  const [options2, setOptions2] = useState<
    Array<{ label: string; value: string }>
  >([]);

  const watchSelect1 = watch(`data.${name1}`);

  useEffect(() => {
    unregister(
      isLink ? ["data.area", "data.cluster"] : ["data.area1", "data.area2"]
    );
    setValue(`data.${name1}`, "");
    setValue(`data.${name2}`, "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLink]);

  useEffect(() => {
    const index = linksOrClusters.findIndex(
      (elm) => elm.element.id === watchSelect1
    );
    if (index >= 0) {
      setOptions2(
        linksOrClusters[index].item_list
          .filter(
            (elm) =>
              !isTermExist(
                constraintsTerm,
                dataToId(
                  isLink
                    ? {
                        area1: watchSelect1,
                        area2: elm.id,
                      }
                    : { area: watchSelect1, cluster: elm.id }
                )
              )
          )
          .map((elm) => ({
            label: elm.name,
            value: elm.id,
          }))
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchSelect1]);

  return (
    <>
      <SelectFE
        name={`data.${name1}`}
        label={t(`study.${name1}`)}
        options={options1}
        control={control}
        rules={{
          required: t("form.field.required") as string,
        }}
        sx={{ minWidth: "200px", height: "60px" }}
      />
      <SelectFE
        name={`data.${name2}`}
        label={t(`study.${name2}`)}
        options={options2}
        control={control}
        rules={{
          required: t("form.field.required") as string,
        }}
        sx={{ minWidth: "200px", ml: 1, height: "60px" }}
      />
    </>
  );
}
