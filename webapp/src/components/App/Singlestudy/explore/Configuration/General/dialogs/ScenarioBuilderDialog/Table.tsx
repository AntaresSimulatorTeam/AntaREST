import { useContext } from "react";
import { useTranslation } from "react-i18next";
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
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { AxiosError } from "axios";

interface Props {
  config: GenericScenarioConfig | ClustersHandlerReturn;
  type: ScenarioType;
  areaId?: string;
}

function Table({ config, type, areaId }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { studyId } = useContext(ScenarioBuilderContext);

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

    try {
      await updateScenarioBuilderConfig(studyId, newData);
    } catch (error) {
      enqueueErrorSnackbar(
        t("study.configuration.general.mcScenarioBuilder.update.error", {
          type,
        }),
        error as AxiosError,
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (Object.keys(config).length === 0) {
    return <SimpleContent title="No scenario configuration." />;
  }

  return (
    <TableForm
      key={JSON.stringify(config)}
      autoSubmit={false}
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
