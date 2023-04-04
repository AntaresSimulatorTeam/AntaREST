import { useContext, useMemo } from "react";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import { Path } from "ramda";
import { LinkElement } from "../../../../../../../../../common/types";
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
import { updateScenarioBuilderConfig } from "../utils";
import { SubmitHandlerPlus } from "../../../../../../../../common/Form/types";
import useEnqueueErrorSnackbar from "../../../../../../../../../hooks/useEnqueueErrorSnackbar";

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
  nbYears: number;
  symbol: string;
  rowType: RowType;
  areaId?: string;
}

function Table(props: Props) {
  const { nbYears, symbol, rowType, areaId } = props;
  const { config, setConfig, reloadConfig, activeRuleset, studyId } =
    useContext(ConfigContext);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const valuesFromConfig = R.path(
    [activeRuleset, symbol, rowType === "thermal" && areaId].filter(
      Boolean
    ) as Path,
    config
  ) as TableData;

  const { data: areasOrLinksOrThermals = [] } = useStudySynthesis({
    studyId,
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
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<TableData>) => {
    const newData = {
      [activeRuleset]: {
        [symbol]:
          rowType === "thermal" && areaId
            ? { [areaId]: dirtyValues }
            : dirtyValues,
      },
    };

    setConfig(R.mergeDeepLeft(newData));

    updateScenarioBuilderConfig(studyId, newData).catch((err) => {
      reloadConfig();
      enqueueErrorSnackbar(
        t("study.configuration.general.mcScenarioBuilder.error.table", [
          `${activeRuleset}.${symbol}`,
        ]),
        err
      );
    });
  };

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
        stretchH: "all",
        className: "htCenter",
      }}
      onSubmit={handleSubmit}
    />
  );
}

export default Table;
