import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { AllClustersAndLinks } from "../../../../../../../../common/types";
import SelectSingle from "../../../../../../../common/SelectSingle";
import { ConstraintTerm, generateTermId, isTermExist } from "../utils";

interface Props {
  list: AllClustersAndLinks;
  isLink: boolean;
  term: ConstraintTerm;
  constraintTerms: ConstraintTerm[];
  saveValue: (constraint: Partial<ConstraintTerm>) => void;
  value1: string;
  value2: string;
  setValue1: (value: string) => void;
  setValue2: (value: string) => void;
}

export default function OptionsList(props: Props) {
  const {
    list,
    isLink,
    term,
    value1,
    value2,
    constraintTerms,
    saveValue,
    setValue1,
    setValue2,
  } = props;
  const [t] = useTranslation();
  const name1 = isLink ? "area1" : "area";
  const name2 = isLink ? "area2" : "cluster";
  const options = isLink ? list.links : list.clusters;
  const options1 = useMemo(() => {
    return options.map((elm) => ({
      name: elm.element.name,
      id: elm.element.id,
    }));
  }, [options]);

  const options2 = useMemo(() => {
    const index = options.findIndex((elm) => elm.element.id === value1);
    if (index < 0) {
      return [];
    }

    const tmp = options[index].item_list
      .filter(
        (elm) =>
          elm.id === value2 ||
          !isTermExist(
            constraintTerms,
            generateTermId(
              isLink
                ? {
                    area1: value1,
                    area2: elm.id,
                  }
                : { area: value1, cluster: elm.id },
            ),
          ),
      )
      .map((elm) => ({
        name: elm.name,
        id: elm.id.toLowerCase(),
      }));
    return tmp;
  }, [constraintTerms, isLink, options, value1, value2]);

  const getFirstValue2 = useCallback(
    (value: string): string => {
      const index = options1.findIndex((elm) => elm.id === value);
      if (index >= 0) {
        return options[index].item_list[0].id;
      }
      return "";
    },
    [options, options1],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleValue1 = useCallback(
    (value: string) => {
      const v2 = getFirstValue2(value);
      saveValue({
        id: term.id,
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
    },
    [term.id, getFirstValue2, isLink, saveValue, setValue1, setValue2],
  );

  const handleValue2 = useCallback(
    (value: string) => {
      setValue2(value);
      saveValue({
        id: term.id,
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
    },
    [term.id, isLink, saveValue, setValue2, value1],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////
  return (
    <>
      <SelectSingle
        name="value1"
        list={options1}
        label={t(`study.${name1}`)}
        size="small"
        variant="outlined"
        data={value1}
        handleChange={(key, value) => handleValue1(value as string)}
        sx={{
          width: 200,
          mr: 1,
        }}
      />
      <SelectSingle
        name="value2"
        list={options2}
        label={t(`study.${name2}`)}
        size="small"
        variant="outlined"
        data={value2.toLowerCase()}
        handleChange={(key, value) => handleValue2(value as string)}
        sx={{
          width: 200,
        }}
      />
    </>
  );
}
