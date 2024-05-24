import { useContext } from "react";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import TableForm from "../../../../../../../common/TableForm";
import { ScenarioBuilderContext } from "./ScenarioBuilderContext";
import {
  GenericScenarioConfig,
  ScenarioType,
  ClustersHandlerReturn,
  updateScenarioBuilderConfig,
} from "./utils";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import SimpleContent from "../../../../../../../common/page/SimpleContent";

interface Props {
  config: GenericScenarioConfig | ClustersHandlerReturn;
  type: ScenarioType;
  areaId?: string;
}

function Table({ config, type, areaId }: Props) {
  const { t } = useTranslation();

  const { setConfig, refreshConfig, isConfigLoading, studyId } = useContext(
    ScenarioBuilderContext,
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ dirtyValues }: SubmitHandlerPlus) => {
    const newData = {
      [type]:
        (type === "thermal" || type === "renewable") && areaId
          ? { [areaId]: dirtyValues }
          : dirtyValues,
    };

    setConfig(R.mergeDeepLeft(newData));

    try {
      await updateScenarioBuilderConfig(studyId, newData);
    } catch (err) {
      refreshConfig();

      throw new Error( // TODO snackbar + update keys
        t("study.configuration.general.mcScenarioBuilder.error.table"),
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  console.log("! isConfigLoading", !isConfigLoading);

  if (!isConfigLoading && Object.keys(config).length === 0) {
    return <SimpleContent title="No scenario configuration" />;
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
