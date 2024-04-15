import { useContext } from "react";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import TableForm from "../../../../../../../common/TableForm";
import { ScenarioBuilderContext } from "./ScenarioBuilderContext";
import {
  GenericScenarioConfig,
  ScenarioSymbol,
  ThermalHandlerReturn,
  updateScenarioBuilderConfig,
} from "./utils";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";

interface Props {
  config: GenericScenarioConfig | ThermalHandlerReturn;
  symbol: ScenarioSymbol;
  areaId?: string;
}

function Table({ config, symbol, areaId }: Props) {
  const { t } = useTranslation();

  const { activeRuleset, setConfig, refreshConfig, studyId } = useContext(
    ScenarioBuilderContext,
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ dirtyValues }: SubmitHandlerPlus) => {
    const newData = {
      [activeRuleset]: {
        [symbol]:
          symbol === "t" && areaId ? { [areaId]: dirtyValues } : dirtyValues,
      },
    };

    setConfig(R.mergeDeepLeft(newData));

    try {
      await updateScenarioBuilderConfig(studyId, newData);
    } catch (err) {
      refreshConfig();

      throw new Error( // TODO snackbar
        t("study.configuration.general.mcScenarioBuilder.error.table", {
          0: `${activeRuleset}.${symbol}`,
        }),
        { cause: err },
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!config) {
    return <div>No configuration available</div>;
  }

  return (
    <TableForm
      key={JSON.stringify(config)}
      defaultValues={config}
      tableProps={{
        type: "numeric",
        placeholder: "rand",
        allowEmpty: true,
        colHeaders: (index) =>
          `${t("study.configuration.general.mcScenarioBuilder.year")} ${
            index + 1
          }`,
        className: "htCenter",
      }}
      onSubmit={handleSubmit}
    />
  );
}

export default Table;
