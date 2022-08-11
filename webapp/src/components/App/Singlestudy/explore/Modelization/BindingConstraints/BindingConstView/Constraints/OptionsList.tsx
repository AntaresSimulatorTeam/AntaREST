import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  AllClustersAndLinks,
  ClusterElement,
  LinkCreationInfoDTO,
} from "../../../../../../../../common/types";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import { useFormContext } from "../../../../../../../common/Form";
import { BindingConstFields, ConstraintType } from "../utils";

interface Props {
  list: AllClustersAndLinks;
  isLink: boolean;
  constraint: ConstraintType;
  index: number;
  saveValue: (constraint: ConstraintType) => void;
}

export default function OptionsList(props: Props) {
  const { control } = useFormContext<BindingConstFields>();
  const { list, isLink, constraint, index, saveValue } = props;
  const [t] = useTranslation();
  console.log("OPTIONS LIST: ", index);
  const value1 = useMemo(
    () =>
      isLink
        ? (constraint.data as LinkCreationInfoDTO).area1
        : (constraint.data as ClusterElement).area,
    [constraint.data, isLink]
  );
  const name1 = useMemo(() => (isLink ? "area1" : "area"), [isLink]);
  const name2 = useMemo(() => (isLink ? "area2" : "cluster"), [isLink]);
  const options = useMemo(
    () => (isLink ? list.links : list.clusters),
    [isLink, list.clusters, list.links]
  );
  const options1 = useMemo(() => {
    return options.map((elm) => ({
      label: elm.element.name,
      value: elm.element.id,
    }));
  }, [options]);

  const options2 = useMemo(() => {
    const index = options.findIndex((elm) => elm.element.id === value1);
    if (index >= 0)
      return options[index].item_list.map((elm) => ({
        label: elm.name,
        value: elm.id,
      }));
    return [];
  }, [options, value1]);

  const getFirstValue2 = useCallback(
    (value: string): string => {
      const index = options1.findIndex((elm) => elm.value === value);
      if (index >= 0) return options[index].item_list[0].id;
      return "";
    },
    [options, options1]
  );

  return (
    <>
      <SelectFE
        name={`constraints.${index}.data.${name1}`}
        label={t(`study.${name1}`)}
        options={options1}
        control={control}
        rules={{
          onAutoSubmit: (value) =>
            saveValue({
              ...constraint,
              data: isLink
                ? {
                    area1: value,
                    area2: getFirstValue2(value),
                  }
                : {
                    area: value,
                    cluster: getFirstValue2(value),
                  },
            }),
        }}
        sx={{ flexGrow: 1, height: "60px" }}
      />
      <SelectFE
        name={`constraints.${index}.data.${name2}`}
        label={t(`study.${name2}`)}
        options={options2}
        control={control}
        rules={{
          onAutoSubmit: (value) =>
            saveValue({
              ...constraint,
              data: isLink
                ? {
                    area1: value1,
                    area2: value,
                  }
                : {
                    area: value1,
                    cluster: value,
                  },
            }),
        }}
        sx={{ flexGrow: 1, height: "60px" }}
      />
    </>
  );
}
