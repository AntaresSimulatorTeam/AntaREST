import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import Fieldset from "../../../../../common/Fieldset";
import { useFormContext } from "../../../../../common/Form";
import {
  AdvancedParamsFormFields,
  HYDRO_HEURISTIC_POLICY_OPTIONS,
  INITIAL_RESERVOIR_OPTIONS,
  HYDRO_PRICING_MODE_OPTIONS,
  POWER_FLUCTUATIONS_OPTIONS,
  SPATIAL_CORRELATIONS_OPTIONS,
  SHEDDING_POLICY_OPTIONS,
  RESERVE_MANAGEMENT_OPTIONS,
  UNIT_COMMITMENT_MODE_OPTIONS,
  SIMULATION_CORES_OPTIONS,
  RENEWABLE_GENERATION_OPTIONS,
} from "./utils";

interface Props {
  version: number;
}

function Fields(props: Props) {
  const [t] = useTranslation();
  const { control } = useFormContext<AdvancedParamsFormFields>();
  const { version } = props;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box>
      <Fieldset
        legend={t(
          "study.configuration.advancedParameters.seedsForRandomNumbers"
        )}
      >
        <NumberFE
          label={t(
            "study.configuration.advancedParameters.windTimeSeriesGeneration"
          )}
          name="seedTsgenWind"
          control={control}
        />
        <NumberFE
          label={t(
            "study.configuration.advancedParameters.loadTimeSeriesGeneration"
          )}
          name="seedTsgenLoad"
          control={control}
        />
        <NumberFE
          label={t(
            "study.configuration.advancedParameters.hydroTimeSeriesGeneration"
          )}
          name="seedTsgenHydro"
          control={control}
        />
        <NumberFE
          label={t(
            "study.configuration.advancedParameters.thermalTimeSeriesGeneration"
          )}
          name="seedTsgenThermal"
          control={control}
        />
        <NumberFE
          label={t(
            "study.configuration.advancedParameters.solarTimeSeriesGeneration"
          )}
          name="seedTsgenSolar"
          control={control}
        />
        <NumberFE
          label={t("study.configuration.advancedParameters.timeSeriesDraws")}
          name="seedTsnumbers"
          control={control}
        />
        <NumberFE
          label={t(
            "study.configuration.advancedParameters.noiseOnUnsuppliedEnergyCosts"
          )}
          name="seedUnsuppliedEnergyCosts"
          control={control}
        />
        <NumberFE
          label={t(
            "study.configuration.advancedParameters.noiseOnSpilledEnergyCosts"
          )}
          name="seedSpilledEnergyCosts"
          control={control}
        />
        <NumberFE
          label={t(
            "study.configuration.advancedParameters.noiseOnThermalPlantsCosts"
          )}
          name="seedThermalCosts"
          control={control}
        />
        <NumberFE
          label={t(
            "study.configuration.advancedParameters.noiseOnVirtualHydroCosts"
          )}
          name="seedHydroCosts"
          control={control}
        />
        <NumberFE
          label={t(
            "study.configuration.advancedParameters.seedInitialReservoirLevels"
          )}
          name="seedInitialReservoirLevels"
          control={control}
        />
      </Fieldset>

      <Fieldset
        legend={t(
          "study.configuration.advancedParameters.spatialTimeSeriesCorrelation"
        )}
      >
        <SelectFE
          multiple
          label={t(
            "study.configuration.advancedParameters.accuracyOnCorrelation"
          )}
          options={SPATIAL_CORRELATIONS_OPTIONS}
          name="accuracyOnCorrelation"
          control={control}
        />
      </Fieldset>

      <Fieldset
        legend={t("study.configuration.advancedParameters.otherPreferences")}
      >
        <SelectFE
          label={t(
            "study.configuration.advancedParameters.initialReservoirLevels"
          )}
          options={INITIAL_RESERVOIR_OPTIONS}
          name="initialReservoirLevels"
          control={control}
        />
        <SelectFE
          label={t(
            "study.configuration.advancedParameters.hydroHeuristicPolicy"
          )}
          options={HYDRO_HEURISTIC_POLICY_OPTIONS}
          name="hydroHeuristicPolicy"
          control={control}
        />
        <SelectFE
          label={t("study.configuration.advancedParameters.hydroPricingMode")}
          options={HYDRO_PRICING_MODE_OPTIONS}
          name="hydroPricingMode"
          control={control}
        />
        <SelectFE
          label={t("study.configuration.advancedParameters.powerFluctuations")}
          options={POWER_FLUCTUATIONS_OPTIONS}
          name="powerFluctuations"
          control={control}
        />
        <SelectFE
          label={t("study.configuration.advancedParameters.sheddingPolicy")}
          options={SHEDDING_POLICY_OPTIONS}
          name="sheddingPolicy"
          control={control}
        />
        <SelectFE
          label={t(
            "study.configuration.advancedParameters.dayAheadReserveManagement"
          )}
          options={RESERVE_MANAGEMENT_OPTIONS}
          name="dayAheadReserveManagement"
          control={control}
        />
        <SelectFE
          label={t("study.configuration.advancedParameters.unitCommitmentMode")}
          options={UNIT_COMMITMENT_MODE_OPTIONS}
          name="unitCommitmentMode"
          control={control}
        />
        <SelectFE
          label={t("study.configuration.advancedParameters.simulationCores")}
          options={SIMULATION_CORES_OPTIONS}
          name="numberOfCoresMode"
          control={control}
        />
        {version >= 810 && (
          <SelectFE
            label={t(
              "study.configuration.advancedParameters.renewableGenerationModeling"
            )}
            options={RENEWABLE_GENERATION_OPTIONS}
            name="renewableGenerationModelling"
            control={control}
          />
        )}
      </Fieldset>
    </Box>
  );
}

export default Fields;
