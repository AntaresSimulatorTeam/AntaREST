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
  selectedArea: string;
  selectedClusterOrArea2: string;
  setSelectedArea: (value: string) => void;
  setSelectedClusterOrArea2: (value: string) => void;
}

export default function OptionsList({
  list,
  isLink,
  term,
  constraintTerms,
  saveValue,
  selectedArea,
  selectedClusterOrArea2,
  setSelectedArea,
  setSelectedClusterOrArea2,
}: Props) {
  const [t] = useTranslation();
  const primaryLabel = isLink ? "area1" : "area";
  const secondaryLabel = isLink ? "area2" : "cluster";

  const options = isLink ? list.links : list.clusters;
  const options1 = useMemo(() => {
    return options.map((elm) => ({
      name: elm.element.name,
      id: elm.element.id,
    }));
  }, [options]);

  const options2 = useMemo(() => {
    const index = options.findIndex((elm) => elm.element.id === selectedArea);
    if (index < 0) {
      return [];
    }

    const tmp = options[index].item_list
      .filter(
        (elm) =>
          elm.id === selectedClusterOrArea2 ||
          !isTermExist(
            constraintTerms,
            generateTermId(
              isLink
                ? {
                    area1: selectedArea,
                    area2: elm.id,
                  }
                : { area: selectedArea, cluster: elm.id },
            ),
          ),
      )
      .map((elm) => ({
        name: elm.name,
        id: elm.id.toLowerCase(),
      }));
    return tmp;
  }, [constraintTerms, isLink, options, selectedArea, selectedClusterOrArea2]);

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
      setSelectedArea(value);
      setSelectedClusterOrArea2(v2);
    },
    [
      term.id,
      getFirstValue2,
      isLink,
      saveValue,
      setSelectedArea,
      setSelectedClusterOrArea2,
    ],
  );

  const handleValue2 = useCallback(
    (value: string) => {
      setSelectedClusterOrArea2(value);
      saveValue({
        id: term.id,
        data: isLink
          ? {
              area1: selectedArea,
              area2: value,
            }
          : {
              area: selectedArea,
              cluster: value,
            },
      });
    },
    [term.id, isLink, saveValue, setSelectedClusterOrArea2, selectedArea],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////
  return (
    <>
      <SelectSingle
        name="selectedArea"
        disabled
        list={options1}
        label={t(`study.${primaryLabel}`)}
        size="small"
        variant="outlined"
        data={selectedArea}
        handleChange={(key, value) => handleValue1(value as string)}
        sx={{
          width: 200,
          mr: 1,
        }}
      />
      <SelectSingle
        name="selectedClusterOrArea2"
        list={options2}
        label={t(`study.${secondaryLabel}`)}
        size="small"
        variant="outlined"
        data={selectedClusterOrArea2.toLowerCase()}
        handleChange={(key, value) => handleValue2(value as string)}
        sx={{
          width: 200,
        }}
      />
    </>
  );
}
