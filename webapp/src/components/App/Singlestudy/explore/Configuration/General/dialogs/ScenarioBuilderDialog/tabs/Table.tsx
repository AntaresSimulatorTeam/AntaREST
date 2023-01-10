import { useContext, useMemo } from "react";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import { Path } from "ramda";
import {
  LinkElement,
  StudyMetadata,
} from "../../../../../../../../../common/types";
import useStudySynthesis, {
  UseStudySynthesisProps,
} from "../../../../../../../../../redux/hooks/useStudySynthesis";
import {
  getArea,
  getAreas,
  getLinks,
} from "../../../../../../../../../redux/selectors";
import FormTable from "../../../../../../../../common/FormTable";
import ConfigContext from "../ConfigContext";

type ElementList = Array<{
  id: string;
  name: string;
  // In link
  label?: LinkElement["label"];
}>;

type RowValues = Record<string, number | "">;

type TableData = Record<string, RowValues>;

type RowType = "area" | "thermal" | "link";

interface Props {
  study: StudyMetadata;
  nbYears: number;
  symbol: string;
  rowType: RowType;
  areaId?: string;
}

function Table(props: Props) {
  const { study, nbYears, symbol, rowType, areaId } = props;
  const { config, currentRuleset } = useContext(ConfigContext);
  const { t } = useTranslation();

  const valuesFromConfig = R.path(
    [currentRuleset, symbol, rowType === "thermal" && areaId].filter(
      Boolean
    ) as Path,
    config
  ) as TableData;

  const { data: areasOrLinksOrThermals = [] } = useStudySynthesis({
    studyId: study.id,
    selector: R.cond<
      [string],
      UseStudySynthesisProps<ElementList | undefined>["selector"]
    >([
      [R.equals("area"), () => getAreas],
      [R.equals("link"), () => getLinks],
      [
        R.equals("thermal"),
        () => (state, studyId) =>
          areaId ? getArea(state, studyId, areaId)?.thermals : undefined,
      ],
    ])(rowType),
  });

  const defaultValues = useMemo(() => {
    const emptyCols = Array.from({ length: nbYears }).reduce(
      (acc: RowValues, _, index) => {
        acc[String(index)] = "";
        return acc;
      },
      {}
    );

    return areasOrLinksOrThermals.reduce((acc: TableData, { id }) => {
      acc[id] = {
        ...emptyCols,
        ...valuesFromConfig?.[id],
      };
      return acc;
    }, {});
  }, [areasOrLinksOrThermals, nbYears, valuesFromConfig]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormTable
      key={JSON.stringify(defaultValues)}
      defaultValues={defaultValues}
      tableProps={{
        type: "numeric",
        placeholder: "rand",
        allowEmpty: true,
        rowHeaders: (row) => {
          const item = areasOrLinksOrThermals.find(({ id }) => row.id === id);
          return item ? item.label || item.name : String(row.id);
        },
        colHeaders: (index) =>
          `${t("study.configuration.general.mcScenarioBuilder.year")} ${
            index + 1
          }`,
        height: "100%",
        stretchH: "all",
        className: "htCenter",
      }}
      onSubmit={({ dirtyValues }) => {
        console.log(dirtyValues);
      }}
    />
  );
}

export default Table;
