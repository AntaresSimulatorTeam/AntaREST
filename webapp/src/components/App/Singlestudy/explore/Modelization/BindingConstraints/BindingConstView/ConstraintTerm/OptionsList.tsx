import { useCallback, useMemo } from "react";
import _ from "lodash";
import { useTranslation } from "react-i18next";
import { AllClustersAndLinks } from "../../../../../../../../common/types";
import SelectSingle from "../../../../../../../common/SelectSingle";
import { ConstraintType } from "../utils";
import { DEBOUNCE_DELAY } from ".";

interface Props {
  list: AllClustersAndLinks;
  isLink: boolean;
  constraint: ConstraintType;
  saveValue: (constraint: Partial<ConstraintType>) => void;
  value1: string;
  value2: string;
  setValue1: (value: string) => void;
  setValue2: (value: string) => void;
}

export default function OptionsList(props: Props) {
  const {
    list,
    isLink,
    constraint,
    value1,
    value2,
    saveValue,
    setValue1,
    setValue2,
  } = props;
  const [t] = useTranslation();
  const name1 = useMemo(() => (isLink ? "area1" : "area"), [isLink]);
  const name2 = useMemo(() => (isLink ? "area2" : "cluster"), [isLink]);
  const options = useMemo(
    () => (isLink ? list.links : list.clusters),
    [isLink, list.clusters, list.links]
  );
  const options1 = useMemo(() => {
    return options.map((elm) => ({
      name: elm.element.name,
      id: elm.element.id,
    }));
  }, [options]);

  const options2 = useMemo(() => {
    const index = options.findIndex((elm) => elm.element.id === value1);
    if (index >= 0)
      return options[index].item_list.map((elm) => ({
        name: elm.name,
        id: elm.id,
      }));
    return [];
  }, [options, value1]);

  const getFirstValue2 = useCallback(
    (value: string): string => {
      const index = options1.findIndex((elm) => elm.id === value);
      if (index >= 0) return options[index].item_list[0].id;
      return "";
    },
    [options, options1]
  );

  const handleValue1 = _.debounce((value: string) => {
    const v2 = getFirstValue2(value);
    saveValue({
      id: constraint.id,
      data: isLink
        ? {
            area1: value,
            area2: v2,
          }
        : {
            area: value,
            cluster: v2,
          },
    });
    setValue1(value);
    setValue2(v2);
  }, DEBOUNCE_DELAY);

  const handleValue2 = _.debounce((value: string) => {
    setValue2(value);
    saveValue({
      id: constraint.id,
      data: isLink
        ? {
            area1: value1,
            area2: value,
          }
        : {
            area: value1,
            cluster: value,
          },
    });
  }, DEBOUNCE_DELAY);

  return (
    <>
      <SelectSingle
        name="value1"
        list={options1}
        label={t(`study.${name1}`)}
        data={value1}
        handleChange={(key, value) => handleValue1(value as string)}
        sx={{
          flexGrow: 1,
          height: "60px",
        }}
      />
      <SelectSingle
        name="value2"
        list={options2}
        label={t(`study.${name2}`)}
        data={value2}
        handleChange={(key, value) => handleValue2(value as string)}
        sx={{
          flexGrow: 1,
          height: "60px",
        }}
      />
    </>
  );
}
